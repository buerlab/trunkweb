'use strict';
var LIVERELOAD_PORT = 35729;
var SERVER_PORT = 9000;
var lrSnippet = require('connect-livereload')({port: LIVERELOAD_PORT});

var mountFolder = function (connect, dir) {
    return connect.static(require('path').resolve(dir));
};

// # Globbing
// for performance reasons we're only matching one level down:
// 'test/spec/{,*/}*.js'
// use this if you want to match all subfolders:
// 'test/spec/**/*.js'
// templateFramework: 'lodash'
    
module.exports = function (grunt) {
    // show elapsed time at the end
    require('time-grunt')(grunt);
    // load all grunt tasks
    require('load-grunt-tasks')(grunt);


    // configurable paths
    var yeomanConfig = {
        app: 'app',
        dist: 'trunkserver/admin_dist',
        fixtures:'app/fixtures',
        tmp:".tmp"
    };

    grunt.initConfig({
        yeoman: yeomanConfig,
        watch: {
            options: {
                nospawn: true,
                livereload: true
            },
            compass: {
                files: ['<%= yeoman.app %>/styles/{,*/}*.{scss,sass}',
                        '<%= yeoman.app %>/bower_components/sass-bootstrap/lib/*.scss'],
                tasks: ['compass','htmlmin','useminPrepare','usemin',"tornado"]
            },
            livereload: {
                options: {
                    livereload: grunt.option('livereloadport') || LIVERELOAD_PORT
                },
                files: [
                    '<%= yeoman.app %>/*.html',
                    '{.tmp,<%= yeoman.app %>}/styles/{,*/}*.css',
                    '{.tmp,<%= yeoman.app %>}/scripts/{,*/}*.js',
                    '<%= yeoman.app %>/images/{,*/}*.{png,jpg,jpeg,gif,webp}',
                    '<%= yeoman.app %>/scripts/templates/*.{ejs,mustache,hbs}',
                    'test/spec/**/*.js'
                ]
            },
            jst: {
                files: [
                    '<%= yeoman.app %>/scripts/templates/*.ejs'
                ],
                tasks: ['jst']
            },
            // test: {
            //     files: ['<%= yeoman.app %>/scripts/{,*/}*.js', 'test/spec/**/*.js'],
            //     tasks: ['test:true']
            // },
            htmlbuild:{
                files: ['<%= yeoman.app %>/nativeHTML/*.html',
                        '<%= yeoman.app %>/fixtures/{,*/}*'
                        ],
                tasks: ['htmlbuild','htmlmin','useminPrepare','usemin',"tornado"]
            },
            js:{
                files:['{.tmp,<%= yeoman.app %>}/scripts/{,*/}*.js'],
                tasks: [
                    'useminPrepare',
                    // 'imagemin',
                    'htmlmin',
                    'concat',
                     // 'cssmin',
                    // 'uglify',
                    // 'copy',
                    // 'rev',
                    'usemin',
                    "tornado"
                ]
            }
        },
        connect: {
            options: {
                port: grunt.option('port') || SERVER_PORT,
                // change this to '0.0.0.0' to access the server from outside
                hostname: 'localhost'
            },
            livereload: {
                options: {
                    port: 9000,
                    middleware: function (connect) {
                        return [
                            lrSnippet,
                            mountFolder(connect, '.tmp'),
                            mountFolder(connect, yeomanConfig.app)
                        ];
                    }
                }
            },
            test: {
                options: {
                    port: 9001,
                    middleware: function (connect) {
                        return [
                            lrSnippet,
                            mountFolder(connect, '.tmp'),
                            mountFolder(connect, 'test'),
                            mountFolder(connect, yeomanConfig.app)
                        ];
                    }
                }
            },
            dist: {
                options: {
                    port: 9289,
                    middleware: function (connect) {
                        return [
                            lrSnippet,
                            mountFolder(connect, yeomanConfig.dist)
                        ];
                    }
                }
            }
        },
        open: {
            livereload: {
                path: 'http://localhost:<%= connect.livereload.options.port %>'
            },
            server: {
                path: 'http://localhost:<%= connect.dist.options.port %>'
            },
            test: {
                path: 'http://localhost:<%= connect.test.options.port %>'
            }
        },
        clean: {
            dist: ['.tmp', '<%= yeoman.dist %>/*'],
            server: '.tmp'
        },
        jshint: {
            options: {
                jshintrc: '.jshintrc',
                reporter: require('jshint-stylish')
            },
            all: [
                'Gruntfile.js',
                '<%= yeoman.app %>/scripts/{,*/}*.js',
                '!<%= yeoman.app %>/scripts/vendor/*',
                'test/spec/{,*/}*.js'
            ]
        },
        mocha: {
            all: {
                options: {
                    run: true,
                    src: ['http://localhost:<%= connect.test.options.port %>/index.html']
                }
            }
        },
        compass: {
            options: {
                sassDir: '<%= yeoman.app %>/styles',
                cssDir: '.tmp/styles',
                imagesDir: '<%= yeoman.app %>/images',
                javascriptsDir: '<%= yeoman.app %>/scripts',
                fontsDir: '<%= yeoman.app %>/styles/fonts',
                importPath: '<%= yeoman.app %>/bower_components',
                relativeAssets: true
            },
            dist: {},
            server: {
                options: {
                    debugInfo: true
                }
            }
        },
        // not enabled since usemin task does concat and uglify
        // check index.html to edit your build targets
        // enable this task if you prefer defining your build targets here
        /*uglify: {
            dist: {}
        },*/
        useminPrepare: {
            html: '<%= yeoman.app %>/*.html',
            options: {
                dest: '<%= yeoman.dist %>'
            }
        },
        usemin: {
            html: ['<%= yeoman.dist %>/{,*/}*.html'],
            css: ['<%= yeoman.dist %>/styles/{,*/}*.css'],
            options: {
                dirs: ['<%= yeoman.dist %>']
            }
        },
        imagemin: {
            dist: {
                files: [{
                    expand: true,
                    cwd: '<%= yeoman.app %>/images',
                    src: '{,*/}*.{png,jpg,jpeg}',
                    dest: '<%= yeoman.dist %>/images'
                }]
            }
        },
        cssmin: {
            dist: {
                files: {
                    '<%= yeoman.dist %>/styles/main.css': [
                        '.tmp/styles/{,*/}*.css',
                        '<%= yeoman.app %>/styles/{,*/}*.css'
                    ]
                }
            }
        },
        htmlmin: {
            dist: {
                options: {
                    /*removeCommentsFromCDATA: true,
                    // https://github.com/yeoman/grunt-usemin/issues/44
                    //collapseWhitespace: true,
                    collapseBooleanAttributes: true,
                    removeAttributeQuotes: true,
                    removeRedundantAttributes: true,
                    useShortDoctype: true,
                    removeEmptyAttributes: true,
                    removeOptionalTags: true*/
                },
                files: [{
                    expand: true,
                    cwd: '<%= yeoman.app %>',
                    src: '*.html',
                    dest: '<%= yeoman.dist %>'
                }]
            }
        },
        copy: {
            dist: {
                files: [{
                    expand: true,
                    dot: true,
                    cwd: '<%= yeoman.app %>',
                    dest: '<%= yeoman.dist %>',
                    src: [
                        '*.{ico,txt}',
                        '.htaccess',
                        'images/{,*/}*.{webp,gif}',
                        'styles/fonts/{,*/}*.*',
                        'bower_components/sass-bootstrap/fonts/*.*',
                        'bower_components/iCheck/skins/square/*.*'
                    ]
                }]
            }
        },
        jst: {
            compile: {
                files: {
                    '.tmp/scripts/templates.js': ['<%= yeoman.app %>/scripts/templates/*.ejs']
                }
            }
        },
        rev: {
            dist: {
                files: {
                    src: [
                        '<%= yeoman.dist %>/scripts/{,*/}*.js',
                        '<%= yeoman.dist %>/styles/{,*/}*.css',
                        '<%= yeoman.dist %>/images/{,*/}*.{png,jpg,jpeg,gif,webp}',
                        // '/styles/fonts/{,*/}*.*',
                        // 'bower_components/sass-bootstrap/fonts/*.*',
                        // 'bower_components/iCheck/skins/square/*.*'
                    ]
                }
            }
        },
        htmlbuild: {
            dist: {
                src: ['<%= yeoman.app %>/nativeHTML/*.html'],
                dest: '<%= yeoman.app %>/',

                options: {
                    beautify: true,
                    parseTag: 'htmlbuild',
                    scripts: {
                        bundle: [
                            '<%= yeoman.fixtures %>/scripts/*.js',
                            '!**/main.js',
                        ],
                        main: [
                            '<%= yeoman.app %>/scripts/**/*.js'
                        ]
                    },
                    styles: {
                        bundle: { 
                            cwd: '<%= yeoman.fixtures %>',
                            files: [
                                'css/libs.css',
                                'css/dev.css'
                            ]
                        },
                        test: '<%= yeoman.fixtures %>/css/inline.css'
                    },
                    sections: {
                        bootstrap_ie6_link:'<%= yeoman.fixtures %>/snippets/bootstrap_ie6_link.snippet',
                        compatible:'<%= yeoman.fixtures %>/snippets/compatible.snippet',
                        meta:'<%= yeoman.fixtures %>/snippets/meta.snippet',
                        google_analytics:'<%= yeoman.fixtures %>/snippets/google_analytics.snippet',
                        vendor_plugins:'<%= yeoman.fixtures %>/snippets/vendor_plugins.snippet',
                        views: '<%= yeoman.fixtures %>/views/**/*.html',
                        sendGoods:'<%= yeoman.fixtures %>/views/sendGoods.html',
                        nav:'<%= yeoman.fixtures %>/views/nav.html',
                        templates: '<%= yeoman.fixtures %>/templates/**/*.html',
                        law:'<%= yeoman.fixtures %>/snippets/law.snippet'
                    },
                    data: {
                        version: "0.1.0",
                        title: "默认标题",
                    },
                }
            }
        }
    });
    

    grunt.registerTask('tornado', 'Run tornado server.', function() {
       var spawn = require('child_process').spawn;
       grunt.log.writeln('Starting tornado development server.');
       // stdio: 'inherit' let us see tornado output in grunt
       var PIPE = {stdio: 'inherit'};
       spawn('sh', ['./trunkserver/restart_admin.sh'], PIPE);
    });

    grunt.registerTask('createDefaultTemplate', function () {
        grunt.file.write('.tmp/scripts/templates.js', 'this.JST = this.JST || {};');
    });

    grunt.registerTask('server', function (target) {
        grunt.log.warn('The `server` task has been deprecated. Use `grunt serve` to start a server.');
        grunt.task.run(['serve' + (target ? ':' + target : '')]);
    });

    grunt.registerTask('serve', function (target) {
        if (target === 'dist') {
            return grunt.task.run(['build', 'open:server', 'tornado']);
        }

        if (target === 'test') {
            return grunt.task.run([
                'clean:server',
                'createDefaultTemplate',
                'jst',
                'compass:server',
                'connect:test',
                'open:test',
                'watch'
            ]);
        }

        grunt.task.run([
            'htmlbuild',
            'clean:server',
            'createDefaultTemplate',
            'jst',
            'compass:server',
            // 'connect:livereload',
            'open:server',
            'watch'
        ]);
    });

    grunt.registerTask('test', function (isConnected) {
        isConnected = Boolean(isConnected);
        var testTasks = [
                'htmlbuild',
                'clean:server',
                'createDefaultTemplate',
                'jst',
                'compass',
                'connect:test',
                'mocha',
            ];

        if(!isConnected) {
            return grunt.task.run(testTasks);
        } else {
            // already connected so not going to connect again, remove the connect:test task
            testTasks.splice(testTasks.indexOf('connect:test'), 1);
            return grunt.task.run(testTasks);
        }
    });

    grunt.registerTask('build', [
        'htmlbuild',
        'clean:dist',
        'createDefaultTemplate',
        'jst',
        'compass:dist',
        'useminPrepare',
        'imagemin',
        'htmlmin',
        'concat',
         // 'cssmin',
        // 'uglify',
        'copy',
        // 'rev',
        'usemin'
    ]);

    grunt.registerTask('default', [
        'jshint',
        'test',
        'build'
    ]);
};
