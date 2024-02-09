# Scaling-Snakes!
This is my IaC repo for my home operations on Kubernetes!

## 💻 Machine Preparation

### System requirements

> [!IMPORTANT]
> 1. The default behaviour of k3s is that all nodes are able to run workloads, **including** control nodes. Worker nodes are therefore optional.
> 2. Do you have 3 or more nodes? It is strongly recommended to make 3 of them control nodes for a highly available control plane.
> 3. Running the cluster on Proxmox VE? My thoughts and recommendations about that are documented [here](https://onedr0p.github.io/home-ops/notes/proxmox-considerations.html).

| Role    | Cores    | Memory        | System Disk               |
|---------|----------|---------------|---------------------------|
| Control | 4 _(6*)_ | 8GB _(24GB*)_ | 100GB _(500GB*)_ SSD/NVMe |
| Worker  | 4 _(6*)_ | 8GB _(24GB*)_ | 100GB _(500GB*)_ SSD/NVMe |
| _\* recommended_ |

### Debian for AMD64

1. Download the latest stable release of Debian from [here](https://cdimage.debian.org/debian-cd/current/amd64/iso-dvd), then follow [this guide](https://www.linuxtechi.com/how-to-install-debian-12-step-by-step) to get it installed. Deviations from the guide:

    ```txt
    Choose "Guided - use entire disk"
    Choose "All files in one partition"
    Delete Swap partition
    Uncheck all Debian desktop environment options
    ```

2. [Post install] Remove CD/DVD as apt source

    ```sh
    su -
    sed -i '/deb cdrom/d' /etc/apt/sources.list
    apt update
    exit
    ```

3. [Post install] Enable sudo for your non-root user

    ```sh
    su -
    apt update
    apt install -y sudo
    usermod -aG sudo ${username}
    echo "${username} ALL=(ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/${username}
    exit
    newgrp sudo
    sudo apt update
    ```

4. [Post install] Add SSH keys (or use `ssh-copy-id` on the client that is connecting)

    📍 _First make sure your ssh keys are up-to-date and added to your github account as [instructed](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account)._

    ```sh
    mkdir -m 700 ~/.ssh
    sudo apt install -y curl
    curl https://github.com/${github_username}.keys > ~/.ssh/authorized_keys
    chmod 600 ~/.ssh/authorized_keys
    ```

### Debian for RasPi4

> [!CAUTION]
> 1. It is recommended to have an 8GB RasPi model. Most important is to **boot from an external SSD/NVMe** rather than an SD card. This is [supported natively](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html), however if you have an early model you may need to [update the bootloader](https://www.tomshardware.com/how-to/boot-raspberry-pi-4-usb) first.
> 2. Check the [power requirements](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#power-supply) if using a PoE Hat and a SSD/NVMe dongle.

1. Download the latest stable release of Debian from [here](https://raspi.debian.net/tested-images). _**Do not** use Raspbian or DietPi or any other flavor Linux OS._

2. Flash the image onto an SSD/NVMe drive.

3. Re-mount the drive to your workstation and then do the following (per the [official documentation](https://raspi.debian.net/defaults-and-settings)):

    ```txt
    Open 'sysconf.txt' in a text editor and save it upon updating the information below
      - Change 'root_authorized_key' to your desired public SSH key
      - Change 'root_pw' to your desired root password
      - Change 'hostname' to your desired hostname
    ```

4. Connect SSD/NVMe drive to the Raspberry Pi 4 and power it on.

5. [Post install] SSH into the device with the `root` user and then create a normal user account with `adduser ${username}`

6. [Post install] Follow steps 3 and 4 from [Debian for AMD64](#debian-for-amd64).

7. [Post install] Install `python3` which is needed by Ansible.

    ```sh
    sudo apt install -y python3
    ```

## 🚀 Getting Started

Once you have installed Debian on your nodes, there are six stages to getting a Flux-managed cluster up and runnning.

> [!CAUTION]
> For all stages below the commands **MUST** be ran on your personal workstation within your repository directory

### 🎉 Stage 1: Create a Git repository

1. Create a new **public** repository by clicking the big green "Use this template" button at the top of this page.

2. Clone **your new repo** to you local workstation and `cd` into it.

### 🌱 Stage 2: Setup your local workstation environment

1. Install the most recent version of [task](https://taskfile.dev/), see the task [installation docs](https://taskfile.dev/installation/) for other supported platforms.

    ```sh
    # Brew
    brew install go-task
    ```

2. Install the most recent version of [direnv](https://direnv.net/), see the direnv [installation docs](https://direnv.net/docs/installation.html) for other supported platforms.

    📍 _After installing `direnv` be sure to **[hook it into your shell](https://direnv.net/docs/hook.html)** and after that is done run `direnv allow` while in your repos' directory._

    ```sh
    # Brew
    brew install direnv
    ```

3. Setup a Python virual env and install Ansible by running the following task command.

    📍 _This commands requires Python 3.10+ to be installed_

    ```sh
    # Platform agnostic
    task deps
    ```

4. Install the required tools: [age](https://github.com/FiloSottile/age), [flux](https://toolkit.fluxcd.io/), [cloudflared](https://github.com/cloudflare/cloudflared), [kubectl](https://kubernetes.io/docs/tasks/tools/), [sops](https://github.com/getsops/sops)

   📍 _Not using brew? Make sure to look up how to install the latest version of each of these CLI tools yourself._

    ```sh
    # Brew
    task brew:deps
    ```

### 🔧 Stage 3: Do bootstrap configuration

📍 _Both `bootstrap/vars/config.yaml` and `bootstrap/vars/addons.yaml` files contain necessary information that is **vital** to the bootstrap process._

1. Generate the `bootstrap/vars/config.yaml` and `bootstrap/vars/addons.yaml` configuration files.

    ```sh
    task init
    ```

2. Setup Age private / public key

    📍 _Using [SOPS](https://github.com/getsops/sops) with [Age](https://github.com/FiloSottile/age) allows us to encrypt secrets and use them in Ansible and Flux._

    2a. Create a Age private / public key (this file is gitignored)

      ```sh
      age-keygen -o age.key
      ```

    2b. Fill out the appropriate vars in `bootstrap/vars/config.yaml`

3. Create Cloudflare API Token

    📍 _To use `cert-manager` with the Cloudflare DNS challenge you will need to create a API Token._

   3a. Head over to Cloudflare and create a API Token by going [here](https://dash.cloudflare.com/profile/api-tokens).

   3b. Under the `API Tokens` section click the blue `Create Token` button.

   3c. Click the blue `Use template` button for the `Edit zone DNS` template.

   3d. Name your token something like `home-kubernetes`

   3e. Under `Permissions`, click `+ Add More` and add each permission below:

    ```text
    Zone - DNS - Edit
    Account - Cloudflare Tunnel - Read
    ```

   3f. Limit the permissions to a specific account and zone resources.

   3g. Fill out the appropriate vars in `bootstrap/vars/config.yaml`

4. Create Cloudflare Tunnel

    📍 _To expose services to the internet you will need to create a [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)._

    4a. Authenticate cloudflared to your domain

      ```sh
      cloudflared tunnel login
      ```

    4b. Create the tunnel

      ```sh
      cloudflared tunnel create k8s
      ```

    4c. In the `~/.cloudflared` directory there will be a json file with details you need. Ignore the `cert.pem` file.

    4d. Fill out the appropriate vars in `bootstrap/vars/config.yaml`

5. Complete filling out the rest of the `bootstrap/vars/config.yaml` configuration file.

    5a. Ensure `bootstrap_acme_production_enabled` is set to `false`.

    5b. [Optional] Update `bootstrap/vars/addons.yaml` and enable applications you would like included.

6. Once done run the following command which will verify and generate all the files needed to continue.

    ```sh
    task configure
    ```

> [!IMPORTANT]
> The configure task will create a `./ansible` directory and the following directories under `./kubernetes`.
> ```sh
> 📁 kubernetes      # Kubernetes cluster defined as code
> ├─📁 bootstrap     # Flux installation (not tracked by Flux)
> ├─📁 flux          # Main Flux configuration of repository
> └─📁 apps          # Apps deployed into the cluster grouped by namespace
> ```

### ⚡ Stage 4: Prepare your nodes for k3s

📍 _Here we will be running an Ansible playbook to prepare your nodes for running a Kubernetes cluster._

1. Ensure you are able to SSH into your nodes from your workstation using a private SSH key **without a passphrase** (for example using a SSH agent). This lets Ansible interact with your nodes.

2. Verify Ansible can view your config

    ```sh
    task ansible:list
    ```

3. Verify Ansible can ping your nodes

    ```sh
    task ansible:ping
    ```

4. Run the Ansible prepare playbook (nodes wil reboot when done)

    ```sh
    task ansible:prepare
    ```

### ⛵ Stage 5: Use Ansible to install k3s

📍 _Here we will be running a Ansible Playbook to install [k3s](https://k3s.io/) with [this](https://galaxy.ansible.com/xanmanning/k3s) Ansible galaxy role. If you run into problems, you can run `task ansible:nuke` to destroy the k3s cluster and start over from this point._

1. Verify Ansible can view your config

    ```sh
    task ansible:list
    ```

2. Verify Ansible can ping your nodes

    ```sh
    task ansible:ping
    ```

3. Install k3s with Ansible

    ```sh
    task ansible:install
    ```

4. Verify the nodes are online

    📍 _If this command **fails** you likely haven't configured `direnv` as mentioned previously in the guide._

    ```sh
    kubectl get nodes -o wide
    # NAME           STATUS   ROLES                       AGE     VERSION
    # k8s-0          Ready    control-plane,etcd,master   1h      v1.27.3+k3s1
    # k8s-1          Ready    worker                      1h      v1.27.3+k3s1
    ```

5. The `kubeconfig` for interacting with your cluster should have been created in the root of your repository.

### 🔹 Stage 6: Install Flux in your cluster

📍 _Here we will be installing [flux](https://fluxcd.io/flux/) after some quick bootstrap steps._

1. Verify Flux can be installed

    ```sh
    flux check --pre
    # ► checking prerequisites
    # ✔ kubectl 1.27.3 >=1.18.0-0
    # ✔ Kubernetes 1.27.3+k3s1 >=1.16.0-0
    # ✔ prerequisites checks passed
    ```

2. Push you changes to git

   📍 **Verify** all the `*.sops.yaml` and `*.sops.yaml` files under the `./ansible`, and `./kubernetes` directories are **encrypted** with SOPS

    ```sh
    git add -A
    git commit -m "Initial commit :rocket:"
    git push
    ```

3. Install Flux and sync the cluster to the Git repository

    ```sh
    task cluster:install
    # namespace/flux-system configured
    # customresourcedefinition.apiextensions.k8s.io/alerts.notification.toolkit.fluxcd.io created
    # ...
    ```

4. Verify Flux components are running in the cluster

    ```sh
    kubectl -n flux-system get pods -o wide
    # NAME                                       READY   STATUS    RESTARTS   AGE
    # helm-controller-5bbd94c75-89sb4            1/1     Running   0          1h
    # kustomize-controller-7b67b6b77d-nqc67      1/1     Running   0          1h
    # notification-controller-7c46575844-k4bvr   1/1     Running   0          1h
    # source-controller-7d6875bcb4-zqw9f         1/1     Running   0          1h
    ```

### 🎤 Verification Steps

_Mic check, 1, 2_ - In a few moments applications should be lighting up like Christmas in July 🎄

1. Output all the common resources in your cluster.

    📍 _Feel free to use the provided [cluster tasks](.taskfiles/ClusterTasks.yaml) for validation of cluster resources or continue to get familiar with the `kubectl` and `flux` CLI tools._


    ```sh
    task cluster:resources
    ```

2. ⚠️ It might take `cert-manager` awhile to generate certificates, this is normal so be patient.

3. 🏆 **Congratulations** if all goes smooth you will have a Kubernetes cluster managed by Flux and your Git repository is driving the state of your cluster.

4. 🧠 Now it's time to pause and go get some motel motor oil ☕ and admire you made it this far!

## 📣 Post installation

#### 🌐 Public DNS

The `external-dns` application created in the `networking` namespace will handle creating public DNS records. By default, `echo-server` and the `flux-webhook` are the only subdomains reachable from the public internet. In order to make additional applications public you must set set the correct ingress class name and ingress annotations like in the HelmRelease for `echo-server`.

#### 🏠 Home DNS

`k8s_gateway` will provide DNS resolution to external Kubernetes resources (i.e. points of entry to the cluster) from any device that uses your home DNS server. For this to work, your home DNS server must be configured to forward DNS queries for `${bootstrap_cloudflare_domain}` to `${bootstrap_k8s_gateway_addr}` instead of the upstream DNS server(s) it normally uses. This is a form of **split DNS** (aka split-horizon DNS / conditional forwarding).

> [!TIP]
> Below is how to configure a Pi-hole for split DNS. Other platforms should be similar.
> 1. Apply this file on the server
> ```sh
> # /etc/dnsmasq.d/99-k8s-gateway-forward.conf
> server=/${bootstrap_cloudflare_domain}/${bootstrap_k8s_gateway_addr}
> ```
> 2. Restart dnsmasq on the server.
> 3. Query an internal-only subdomain from your workstation (any `internal` class ingresses): `dig @${home-dns-server-ip} hubble.${bootstrap_cloudflare_domain}`. It should resolve to `${bootstrap_internal_ingress_addr}`.

If you're having trouble with DNS be sure to check out these two GitHub discussions: [Internal DNS](https://github.com/onedr0p/flux-cluster-template/discussions/719) and [Pod DNS resolution broken](https://github.com/onedr0p/flux-cluster-template/discussions/635).

... Nothing working? That is expected, this is DNS after all!

#### 📜 Certificates

By default this template will deploy a wildcard certificate using the Let's Encrypt **staging environment**, which prevents you from getting rate-limited by the Let's Encrypt production servers if your cluster doesn't deploy properly (for example due to a misconfiguration). Once you are sure you will keep the cluster up for more than a few hours be sure to switch to the production servers as outlined in `config.yaml`.

📍 _You will need a production certificate to reach internet-exposed applications through `cloudflared`._

#### 🪝 Github Webhook

By default Flux will periodically check your git repository for changes. In order to have Flux reconcile on `git push` you must configure Github to send `push` events.

1. Obtain the webhook path

    📍 _Hook id and path should look like `/hook/12ebd1e363c641dc3c2e430ecf3cee2b3c7a5ac9e1234506f6f5f3ce1230e123`_

    ```sh
    kubectl -n flux-system get receiver github-receiver -o jsonpath='{.status.webhookPath}'
    ```

2. Piece together the full URL with the webhook path appended

    ```text
    https://flux-webhook.${bootstrap_cloudflare_domain}/hook/12ebd1e363c641dc3c2e430ecf3cee2b3c7a5ac9e1234506f6f5f3ce1230e123
    ```

3. Navigate to the settings of your repository on Github, under "Settings/Webhooks" press the "Add webhook" button. Fill in the webhook url and your `bootstrap_flux_github_webhook_token` secret and save.

### 🤖 Renovate

[Renovate](https://www.mend.io/renovate) is a tool that automates dependency management. It is designed to scan your repository around the clock and open PRs for out-of-date dependencies it finds. Common dependencies it can discover are Helm charts, container images, GitHub Actions, Ansible roles... even Flux itself! Merging a PR will cause Flux to apply the update to your cluster.

To enable Renovate, click the 'Configure' button over at their [Github app page](https://github.com/apps/renovate) and select your repository. Renovate creates a "Dependency Dashboard" as an issue in your repository, giving an overview of the status of all updates. The dashboard has interactive checkboxes that let you do things like advance scheduling or reattempt update PRs you closed without merging.

The base Renovate configuration in your repository can be viewed at [.github/renovate.json5](https://github.com/onedr0p/flux-cluster-template/blob/main/.github/renovate.json5). By default it is scheduled to be active with PRs every weekend, but you can [change the schedule to anything you want](https://docs.renovatebot.com/presets-schedule), or remove it if you want Renovate to open PRs right away.

