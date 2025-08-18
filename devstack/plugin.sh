# magnum.sh - Devstack extras script to install magnum

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set -o xtrace

echo_summary "magnum's plugin.sh was called..."
source $DEST/magnum-capi-helm/devstack/lib/magnum-capi-helm
(set -o posix; set)

if is_service_enabled magnum-api magnum-cond; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing magnum-capi-helm"
        install_magnum_capi_helm
fi

# Restore xtrace
$XTRACE
