{
    "package": {
        "name": "roboschool",
        "repo": "roboschool",
        "subject": "thecrazyt",
        "vcs_url": "https://travis-ci.org/TheCrazyT/roboschool",
        "licenses": ["MIT"]
    },

    "version": {
        "name": "0.6"
    },

    "files":
        [
            {
                "includePattern": "/home/travis/build/TheCrazyT/roboschool/build/(.*)", "uploadPattern": "0.6/$1",
                "matrixParams": {
                    "override": 1 
                }
            }
        ],
    "publish": true
}
