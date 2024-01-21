function cloc
    git count | xargs wc -l 2>/dev/null
end