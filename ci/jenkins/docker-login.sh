_usage="Usage: $0 [--docker-user <dockerUser>] [--docker-password <dockerPassword>]

Run Docker login script.

        --docker-user             Username for Docker account.
        --docker-password         Password for Docker account."

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --docker-user)
    dockerUser="$2"
    shift 2
    ;;
    --docker-password)
    dockerPassword="$2"
    shift 2
    ;;
    -h|--help)
    print_usage
    exit 0
    ;;
    *)    # unknown option
    echoerr "Unknown option $1"
    exit 1
    ;;
esac
done

function docker_login() {
    set +ex
    for i in `seq 5`; do
    # Use --password-stdin to avoid a warning message
        echo $2 docker login --username=$1 --password-stdin
        if [[ "$?" -ne 0 ]]; then
            sleep 5s
            echo "Docker login failed. Retrying"
            continue
        fi
        break
    done
    set -ex
}

docker_login "${dockerUser}" "${dockerPassword}"