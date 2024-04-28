enable_fight_last:
    fd -e toml . config/tasksets -x sed -i -z 's/"fight"\nenabled = false/"fight"\nenabled = true/' {}

disable_fight_last:
    fd -e toml . config/tasksets -x sed -i -z 's/"fight"\nenabled = true/"fight"\nenabled = false/' {}