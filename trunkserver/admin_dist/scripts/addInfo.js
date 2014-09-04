/*!
 * typeahead.js 0.10.2
 * https://github.com/twitter/typeahead.js
 * Copyright 2013-2014 Twitter, Inc. and other contributors; Licensed MIT
 */

(function($) {
    var _ = {
        isMsie: function() {
            return /(msie|trident)/i.test(navigator.userAgent) ? navigator.userAgent.match(/(msie |rv:)(\d+(.\d+)?)/i)[2] : false;
        },
        isBlankString: function(str) {
            return !str || /^\s*$/.test(str);
        },
        escapeRegExChars: function(str) {
            return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
        },
        isString: function(obj) {
            return typeof obj === "string";
        },
        isNumber: function(obj) {
            return typeof obj === "number";
        },
        isArray: $.isArray,
        isFunction: $.isFunction,
        isObject: $.isPlainObject,
        isUndefined: function(obj) {
            return typeof obj === "undefined";
        },
        bind: $.proxy,
        each: function(collection, cb) {
            $.each(collection, reverseArgs);
            function reverseArgs(index, value) {
                return cb(value, index);
            }
        },
        map: $.map,
        filter: $.grep,
        every: function(obj, test) {
            var result = true;
            if (!obj) {
                return result;
            }
            $.each(obj, function(key, val) {
                if (!(result = test.call(null, val, key, obj))) {
                    return false;
                }
            });
            return !!result;
        },
        some: function(obj, test) {
            var result = false;
            if (!obj) {
                return result;
            }
            $.each(obj, function(key, val) {
                if (result = test.call(null, val, key, obj)) {
                    return false;
                }
            });
            return !!result;
        },
        mixin: $.extend,
        getUniqueId: function() {
            var counter = 0;
            return function() {
                return counter++;
            };
        }(),
        templatify: function templatify(obj) {
            return $.isFunction(obj) ? obj : template;
            function template() {
                return String(obj);
            }
        },
        defer: function(fn) {
            setTimeout(fn, 0);
        },
        debounce: function(func, wait, immediate) {
            var timeout, result;
            return function() {
                var context = this, args = arguments, later, callNow;
                later = function() {
                    timeout = null;
                    if (!immediate) {
                        result = func.apply(context, args);
                    }
                };
                callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) {
                    result = func.apply(context, args);
                }
                return result;
            };
        },
        throttle: function(func, wait) {
            var context, args, timeout, result, previous, later;
            previous = 0;
            later = function() {
                previous = new Date();
                timeout = null;
                result = func.apply(context, args);
            };
            return function() {
                var now = new Date(), remaining = wait - (now - previous);
                context = this;
                args = arguments;
                if (remaining <= 0) {
                    clearTimeout(timeout);
                    timeout = null;
                    previous = now;
                    result = func.apply(context, args);
                } else if (!timeout) {
                    timeout = setTimeout(later, remaining);
                }
                return result;
            };
        },
        noop: function() {}
    };
    var VERSION = "0.10.2";
    var tokenizers = function(root) {
        return {
            nonword: nonword,
            whitespace: whitespace,
            chinese:chinese,
            obj: {
                nonword: getObjTokenizer(nonword),
                whitespace: getObjTokenizer(whitespace),
                chinese:getObjTokenizer(chinese)
            }
        };
        function whitespace(s) {
            return s.split(/\s+/);
        }
        function nonword(s) {
            return s.split(/\W+/);
        }
        function chinese(s){
            return s.split("");
        }
        function getObjTokenizer(tokenizer) {
            return function setKey(key) {
                return function tokenize(o) {
                    return tokenizer(o[key]);
                };
            };
        }
    }();
    var LruCache = function() {
        function LruCache(maxSize) {
            this.maxSize = maxSize || 100;
            this.size = 0;
            this.hash = {};
            this.list = new List();
        }
        _.mixin(LruCache.prototype, {
            set: function set(key, val) {
                var tailItem = this.list.tail, node;
                if (this.size >= this.maxSize) {
                    this.list.remove(tailItem);
                    delete this.hash[tailItem.key];
                }
                if (node = this.hash[key]) {
                    node.val = val;
                    this.list.moveToFront(node);
                } else {
                    node = new Node(key, val);
                    this.list.add(node);
                    this.hash[key] = node;
                    this.size++;
                }
            },
            get: function get(key) {
                var node = this.hash[key];
                if (node) {
                    this.list.moveToFront(node);
                    return node.val;
                }
            }
        });
        function List() {
            this.head = this.tail = null;
        }
        _.mixin(List.prototype, {
            add: function add(node) {
                if (this.head) {
                    node.next = this.head;
                    this.head.prev = node;
                }
                this.head = node;
                this.tail = this.tail || node;
            },
            remove: function remove(node) {
                node.prev ? node.prev.next = node.next : this.head = node.next;
                node.next ? node.next.prev = node.prev : this.tail = node.prev;
            },
            moveToFront: function(node) {
                this.remove(node);
                this.add(node);
            }
        });
        function Node(key, val) {
            this.key = key;
            this.val = val;
            this.prev = this.next = null;
        }
        return LruCache;
    }();
    var PersistentStorage = function() {
        var ls, methods;
        try {
            ls = window.localStorage;
            ls.setItem("~~~", "!");
            ls.removeItem("~~~");
        } catch (err) {
            ls = null;
        }
        function PersistentStorage(namespace) {
            this.prefix = [ "__", namespace, "__" ].join("");
            this.ttlKey = "__ttl__";
            this.keyMatcher = new RegExp("^" + this.prefix);
        }
        if (ls && window.JSON) {
            methods = {
                _prefix: function(key) {
                    return this.prefix + key;
                },
                _ttlKey: function(key) {
                    return this._prefix(key) + this.ttlKey;
                },
                get: function(key) {
                    if (this.isExpired(key)) {
                        this.remove(key);
                    }
                    return decode(ls.getItem(this._prefix(key)));
                },
                set: function(key, val, ttl) {
                    if (_.isNumber(ttl)) {
                        ls.setItem(this._ttlKey(key), encode(now() + ttl));
                    } else {
                        ls.removeItem(this._ttlKey(key));
                    }
                    return ls.setItem(this._prefix(key), encode(val));
                },
                remove: function(key) {
                    ls.removeItem(this._ttlKey(key));
                    ls.removeItem(this._prefix(key));
                    return this;
                },
                clear: function() {
                    var i, key, keys = [], len = ls.length;
                    for (i = 0; i < len; i++) {
                        if ((key = ls.key(i)).match(this.keyMatcher)) {
                            keys.push(key.replace(this.keyMatcher, ""));
                        }
                    }
                    for (i = keys.length; i--; ) {
                        this.remove(keys[i]);
                    }
                    return this;
                },
                isExpired: function(key) {
                    var ttl = decode(ls.getItem(this._ttlKey(key)));
                    return _.isNumber(ttl) && now() > ttl ? true : false;
                }
            };
        } else {
            methods = {
                get: _.noop,
                set: _.noop,
                remove: _.noop,
                clear: _.noop,
                isExpired: _.noop
            };
        }
        _.mixin(PersistentStorage.prototype, methods);
        return PersistentStorage;
        function now() {
            return new Date().getTime();
        }
        function encode(val) {
            return JSON.stringify(_.isUndefined(val) ? null : val);
        }
        function decode(val) {
            return JSON.parse(val);
        }
    }();
    var Transport = function() {
        var pendingRequestsCount = 0, pendingRequests = {}, maxPendingRequests = 6, requestCache = new LruCache(10);
        function Transport(o) {
            o = o || {};
            this._send = o.transport ? callbackToDeferred(o.transport) : $.ajax;
            this._get = o.rateLimiter ? o.rateLimiter(this._get) : this._get;
        }
        Transport.setMaxPendingRequests = function setMaxPendingRequests(num) {
            maxPendingRequests = num;
        };
        Transport.resetCache = function clearCache() {
            requestCache = new LruCache(10);
        };
        _.mixin(Transport.prototype, {
            _get: function(url, o, cb) {
                var that = this, jqXhr;
                if (jqXhr = pendingRequests[url]) {
                    jqXhr.done(done).fail(fail);
                } else if (pendingRequestsCount < maxPendingRequests) {
                    pendingRequestsCount++;
                    pendingRequests[url] = this._send(url, o).done(done).fail(fail).always(always);
                } else {
                    this.onDeckRequestArgs = [].slice.call(arguments, 0);
                }
                function done(resp) {
                    cb && cb(null, resp);
                    requestCache.set(url, resp);
                }
                function fail() {
                    cb && cb(true);
                }
                function always() {
                    pendingRequestsCount--;
                    delete pendingRequests[url];
                    if (that.onDeckRequestArgs) {
                        that._get.apply(that, that.onDeckRequestArgs);
                        that.onDeckRequestArgs = null;
                    }
                }
            },
            get: function(url, o, cb) {
                var resp;
                if (_.isFunction(o)) {
                    cb = o;
                    o = {};
                }
                if (resp = requestCache.get(url)) {
                    _.defer(function() {
                        cb && cb(null, resp);
                    });
                } else {
                    this._get(url, o, cb);
                }
                return !!resp;
            }
        });
        return Transport;
        function callbackToDeferred(fn) {
            return function customSendWrapper(url, o) {
                var deferred = $.Deferred();
                fn(url, o, onSuccess, onError);
                return deferred;
                function onSuccess(resp) {
                    _.defer(function() {
                        deferred.resolve(resp);
                    });
                }
                function onError(err) {
                    _.defer(function() {
                        deferred.reject(err);
                    });
                }
            };
        }
    }();
    var SearchIndex = function() {
        function SearchIndex(o) {
            o = o || {};
            if (!o.datumTokenizer || !o.queryTokenizer) {
                $.error("datumTokenizer and queryTokenizer are both required");
            }
            this.datumTokenizer = o.datumTokenizer;
            this.queryTokenizer = o.queryTokenizer;
            this.reset();
        }
        _.mixin(SearchIndex.prototype, {
            bootstrap: function bootstrap(o) {
                this.datums = o.datums;
                this.trie = o.trie;
            },
            add: function(data) {
                var that = this;
                data = _.isArray(data) ? data : [ data ];
                _.each(data, function(datum) {
                    var id, tokens;
                    id = that.datums.push(datum) - 1;
                    tokens = normalizeTokens(that.datumTokenizer(datum));
                    _.each(tokens, function(token) {
                        var node, chars, ch;
                        node = that.trie;
                        chars = token.split("");
                        while (ch = chars.shift()) {
                            node = node.children[ch] || (node.children[ch] = newNode());
                            node.ids.push(id);
                        }
                    });
                });
            },
            get: function get(query) {
                var that = this, tokens, matches;
                tokens = normalizeTokens(this.queryTokenizer(query));
                _.each(tokens, function(token) {
                    var node, chars, ch, ids;
                    if (matches && matches.length === 0) {
                        return false;
                    }
                    node = that.trie;
                    chars = token.split("");
                    while (node && (ch = chars.shift())) {
                        node = node.children[ch];
                    }
                    if (node && chars.length === 0) {
                        ids = node.ids.slice(0);
                        matches = matches ? getIntersection(matches, ids) : ids;
                    } else {
                        matches = [];
                        return false;
                    }
                });
                return matches ? _.map(unique(matches), function(id) {
                    return that.datums[id];
                }) : [];
            },
            reset: function reset() {
                this.datums = [];
                this.trie = newNode();
            },
            serialize: function serialize() {
                return {
                    datums: this.datums,
                    trie: this.trie
                };
            }
        });
        return SearchIndex;
        function normalizeTokens(tokens) {
            tokens = _.filter(tokens, function(token) {
                return !!token;
            });
            tokens = _.map(tokens, function(token) {
                return token.toLowerCase();
            });
            return tokens;
        }
        function newNode() {
            return {
                ids: [],
                children: {}
            };
        }
        function unique(array) {
            var seen = {}, uniques = [];
            for (var i = 0; i < array.length; i++) {
                if (!seen[array[i]]) {
                    seen[array[i]] = true;
                    uniques.push(array[i]);
                }
            }
            return uniques;
        }
        function getIntersection(arrayA, arrayB) {
            var ai = 0, bi = 0, intersection = [];
            arrayA = arrayA.sort(compare);
            arrayB = arrayB.sort(compare);
            while (ai < arrayA.length && bi < arrayB.length) {
                if (arrayA[ai] < arrayB[bi]) {
                    ai++;
                } else if (arrayA[ai] > arrayB[bi]) {
                    bi++;
                } else {
                    intersection.push(arrayA[ai]);
                    ai++;
                    bi++;
                }
            }
            return intersection;
            function compare(a, b) {
                return a - b;
            }
        }
    }();
    var oParser = function() {
        return {
            local: getLocal,
            prefetch: getPrefetch,
            remote: getRemote
        };
        function getLocal(o) {
            return o.local || null;
        }
        function getPrefetch(o) {
            var prefetch, defaults;
            defaults = {
                url: null,
                thumbprint: "",
                ttl: 24 * 60 * 60 * 1e3,
                filter: null,
                ajax: {}
            };
            if (prefetch = o.prefetch || null) {
                prefetch = _.isString(prefetch) ? {
                    url: prefetch
                } : prefetch;
                prefetch = _.mixin(defaults, prefetch);
                prefetch.thumbprint = VERSION + prefetch.thumbprint;
                prefetch.ajax.type = prefetch.ajax.type || "GET";
                prefetch.ajax.dataType = prefetch.ajax.dataType || "json";
                !prefetch.url && $.error("prefetch requires url to be set");
            }
            return prefetch;
        }
        function getRemote(o) {
            var remote, defaults;
            defaults = {
                url: null,
                wildcard: "%QUERY",
                replace: null,
                rateLimitBy: "debounce",
                rateLimitWait: 300,
                send: null,
                filter: null,
                ajax: {}
            };
            if (remote = o.remote || null) {
                remote = _.isString(remote) ? {
                    url: remote
                } : remote;
                remote = _.mixin(defaults, remote);
                remote.rateLimiter = /^throttle$/i.test(remote.rateLimitBy) ? byThrottle(remote.rateLimitWait) : byDebounce(remote.rateLimitWait);
                remote.ajax.type = remote.ajax.type || "GET";
                remote.ajax.dataType = remote.ajax.dataType || "json";
                delete remote.rateLimitBy;
                delete remote.rateLimitWait;
                !remote.url && $.error("remote requires url to be set");
            }
            return remote;
            function byDebounce(wait) {
                return function(fn) {
                    return _.debounce(fn, wait);
                };
            }
            function byThrottle(wait) {
                return function(fn) {
                    return _.throttle(fn, wait);
                };
            }
        }
    }();
    (function(root) {
        var old, keys;
        old = root.Bloodhound;
        keys = {
            data: "data",
            protocol: "protocol",
            thumbprint: "thumbprint"
        };
        root.Bloodhound = Bloodhound;
        function Bloodhound(o) {
            if (!o || !o.local && !o.prefetch && !o.remote) {
                $.error("one of local, prefetch, or remote is required");
            }
            this.limit = o.limit || 5;
            this.sorter = getSorter(o.sorter);
            this.dupDetector = o.dupDetector || ignoreDuplicates;
            this.local = oParser.local(o);
            this.prefetch = oParser.prefetch(o);
            this.remote = oParser.remote(o);
            this.cacheKey = this.prefetch ? this.prefetch.cacheKey || this.prefetch.url : null;
            this.index = new SearchIndex({
                datumTokenizer: o.datumTokenizer,
                queryTokenizer: o.queryTokenizer
            });
            this.storage = this.cacheKey ? new PersistentStorage(this.cacheKey) : null;
        }
        Bloodhound.noConflict = function noConflict() {
            root.Bloodhound = old;
            return Bloodhound;
        };
        Bloodhound.tokenizers = tokenizers;
        _.mixin(Bloodhound.prototype, {
            _loadPrefetch: function loadPrefetch(o) {
                var that = this, serialized, deferred;
                if (serialized = this._readFromStorage(o.thumbprint)) {
                    this.index.bootstrap(serialized);
                    deferred = $.Deferred().resolve();
                } else {
                    deferred = $.ajax(o.url, o.ajax).done(handlePrefetchResponse);
                }
                return deferred;
                function handlePrefetchResponse(resp) {
                    that.clear();
                    that.add(o.filter ? o.filter(resp) : resp);
                    that._saveToStorage(that.index.serialize(), o.thumbprint, o.ttl);
                }
            },
            _getFromRemote: function getFromRemote(query, cb) {
                var that = this, url, uriEncodedQuery;
                query = query || "";
                uriEncodedQuery = encodeURIComponent(query);
                url = this.remote.replace ? this.remote.replace(this.remote.url, query) : this.remote.url.replace(this.remote.wildcard, uriEncodedQuery);
                return this.transport.get(url, this.remote.ajax, handleRemoteResponse);
                function handleRemoteResponse(err, resp) {
                    err ? cb([]) : cb(that.remote.filter ? that.remote.filter(resp) : resp);
                }
            },
            _saveToStorage: function saveToStorage(data, thumbprint, ttl) {
                if (this.storage) {
                    this.storage.set(keys.data, data, ttl);
                    this.storage.set(keys.protocol, location.protocol, ttl);
                    this.storage.set(keys.thumbprint, thumbprint, ttl);
                }
            },
            _readFromStorage: function readFromStorage(thumbprint) {
                var stored = {}, isExpired;
                if (this.storage) {
                    stored.data = this.storage.get(keys.data);
                    stored.protocol = this.storage.get(keys.protocol);
                    stored.thumbprint = this.storage.get(keys.thumbprint);
                }
                isExpired = stored.thumbprint !== thumbprint || stored.protocol !== location.protocol;
                return stored.data && !isExpired ? stored.data : null;
            },
            _initialize: function initialize() {
                var that = this, local = this.local, deferred;
                deferred = this.prefetch ? this._loadPrefetch(this.prefetch) : $.Deferred().resolve();
                local && deferred.done(addLocalToIndex);
                this.transport = this.remote ? new Transport(this.remote) : null;
                return this.initPromise = deferred.promise();
                function addLocalToIndex() {
                    that.add(_.isFunction(local) ? local() : local);
                }
            },
            initialize: function initialize(force) {
                return !this.initPromise || force ? this._initialize() : this.initPromise;
            },
            add: function add(data) {
                this.index.add(data);
            },
            get: function get(query, cb) {
                var that = this, matches = [], cacheHit = false;
                matches = this.index.get(query);
                matches = this.sorter(matches).slice(0, this.limit);
                if (matches.length < this.limit && this.transport) {
                    cacheHit = this._getFromRemote(query, returnRemoteMatches);
                }
                if (!cacheHit) {
                    (matches.length > 0 || !this.transport) && cb && cb(matches);
                }
                function returnRemoteMatches(remoteMatches) {
                    var matchesWithBackfill = matches.slice(0);
                    _.each(remoteMatches, function(remoteMatch) {
                        var isDuplicate;
                        isDuplicate = _.some(matchesWithBackfill, function(match) {
                            return that.dupDetector(remoteMatch, match);
                        });
                        !isDuplicate && matchesWithBackfill.push(remoteMatch);
                        return matchesWithBackfill.length < that.limit;
                    });
                    cb && cb(that.sorter(matchesWithBackfill));
                }
            },
            clear: function clear() {
                this.index.reset();
            },
            clearPrefetchCache: function clearPrefetchCache() {
                this.storage && this.storage.clear();
            },
            clearRemoteCache: function clearRemoteCache() {
                this.transport && Transport.resetCache();
            },
            ttAdapter: function ttAdapter() {
                return _.bind(this.get, this);
            }
        });
        return Bloodhound;
        function getSorter(sortFn) {
            return _.isFunction(sortFn) ? sort : noSort;
            function sort(array) {
                return array.sort(sortFn);
            }
            function noSort(array) {
                return array;
            }
        }
        function ignoreDuplicates() {
            return false;
        }
    })(this);
    var html = {
        wrapper: '<span class="twitter-typeahead"></span>',
        dropdown: '<span class="tt-dropdown-menu"></span>',
        dataset: '<div class="tt-dataset-%CLASS%"></div>',
        suggestions: '<span class="tt-suggestions"></span>',
        suggestion: '<div class="tt-suggestion"></div>'
    };
    var css = {
        wrapper: {
            position: "relative",
            display: "inline-block"
        },
        hint: {
            position: "absolute",
            top: "0",
            left: "0",
            borderColor: "transparent",
            boxShadow: "none"
        },
        input: {
            position: "relative",
            verticalAlign: "top",
            backgroundColor: "transparent"
        },
        inputWithNoHint: {
            position: "relative",
            verticalAlign: "top"
        },
        dropdown: {
            position: "absolute",
            top: "100%",
            left: "0",
            zIndex: "100",
            display: "none"
        },
        suggestions: {
            display: "block"
        },
        suggestion: {
            whiteSpace: "nowrap",
            cursor: "pointer"
        },
        suggestionChild: {
            whiteSpace: "normal"
        },
        ltr: {
            left: "0",
            right: "auto"
        },
        rtl: {
            left: "auto",
            right: " 0"
        }
    };
    if (_.isMsie()) {
        _.mixin(css.input, {
            backgroundImage: "url(data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7)"
        });
    }
    if (_.isMsie() && _.isMsie() <= 7) {
        _.mixin(css.input, {
            marginTop: "-1px"
        });
    }
    var EventBus = function() {
        var namespace = "typeahead:";
        function EventBus(o) {
            if (!o || !o.el) {
                $.error("EventBus initialized without el");
            }
            this.$el = $(o.el);
        }
        _.mixin(EventBus.prototype, {
            trigger: function(type) {
                var args = [].slice.call(arguments, 1);
                this.$el.trigger(namespace + type, args);
            }
        });
        return EventBus;
    }();
    var EventEmitter = function() {
        var splitter = /\s+/, nextTick = getNextTick();
        return {
            onSync: onSync,
            onAsync: onAsync,
            off: off,
            trigger: trigger
        };
        function on(method, types, cb, context) {
            var type;
            if (!cb) {
                return this;
            }
            types = types.split(splitter);
            cb = context ? bindContext(cb, context) : cb;
            this._callbacks = this._callbacks || {};
            while (type = types.shift()) {
                this._callbacks[type] = this._callbacks[type] || {
                    sync: [],
                    async: []
                };
                this._callbacks[type][method].push(cb);
            }
            return this;
        }
        function onAsync(types, cb, context) {
            return on.call(this, "async", types, cb, context);
        }
        function onSync(types, cb, context) {
            return on.call(this, "sync", types, cb, context);
        }
        function off(types) {
            var type;
            if (!this._callbacks) {
                return this;
            }
            types = types.split(splitter);
            while (type = types.shift()) {
                delete this._callbacks[type];
            }
            return this;
        }
        function trigger(types) {
            var type, callbacks, args, syncFlush, asyncFlush;
            if (!this._callbacks) {
                return this;
            }
            types = types.split(splitter);
            args = [].slice.call(arguments, 1);
            while ((type = types.shift()) && (callbacks = this._callbacks[type])) {
                syncFlush = getFlush(callbacks.sync, this, [ type ].concat(args));
                asyncFlush = getFlush(callbacks.async, this, [ type ].concat(args));
                syncFlush() && nextTick(asyncFlush);
            }
            return this;
        }
        function getFlush(callbacks, context, args) {
            return flush;
            function flush() {
                var cancelled;
                for (var i = 0; !cancelled && i < callbacks.length; i += 1) {
                    cancelled = callbacks[i].apply(context, args) === false;
                }
                return !cancelled;
            }
        }
        function getNextTick() {
            var nextTickFn;
            if (window.setImmediate) {
                nextTickFn = function nextTickSetImmediate(fn) {
                    setImmediate(function() {
                        fn();
                    });
                };
            } else {
                nextTickFn = function nextTickSetTimeout(fn) {
                    setTimeout(function() {
                        fn();
                    }, 0);
                };
            }
            return nextTickFn;
        }
        function bindContext(fn, context) {
            return fn.bind ? fn.bind(context) : function() {
                fn.apply(context, [].slice.call(arguments, 0));
            };
        }
    }();
    var highlight = function(doc) {
        var defaults = {
            node: null,
            pattern: null,
            tagName: "strong",
            className: null,
            wordsOnly: false,
            caseSensitive: false
        };
        return function hightlight(o) {
            var regex;
            o = _.mixin({}, defaults, o);
            if (!o.node || !o.pattern) {
                return;
            }
            o.pattern = _.isArray(o.pattern) ? o.pattern : [ o.pattern ];
            regex = getRegex(o.pattern, o.caseSensitive, o.wordsOnly);
            traverse(o.node, hightlightTextNode);
            function hightlightTextNode(textNode) {
                var match, patternNode;
                if (match = regex.exec(textNode.data)) {
                    wrapperNode = doc.createElement(o.tagName);
                    o.className && (wrapperNode.className = o.className);
                    patternNode = textNode.splitText(match.index);
                    patternNode.splitText(match[0].length);
                    wrapperNode.appendChild(patternNode.cloneNode(true));
                    textNode.parentNode.replaceChild(wrapperNode, patternNode);
                }
                return !!match;
            }
            function traverse(el, hightlightTextNode) {
                var childNode, TEXT_NODE_TYPE = 3;
                for (var i = 0; i < el.childNodes.length; i++) {
                    childNode = el.childNodes[i];
                    if (childNode.nodeType === TEXT_NODE_TYPE) {
                        i += hightlightTextNode(childNode) ? 1 : 0;
                    } else {
                        traverse(childNode, hightlightTextNode);
                    }
                }
            }
        };
        function getRegex(patterns, caseSensitive, wordsOnly) {
            var escapedPatterns = [], regexStr;
            for (var i = 0; i < patterns.length; i++) {
                escapedPatterns.push(_.escapeRegExChars(patterns[i]));
            }
            regexStr = wordsOnly ? "\\b(" + escapedPatterns.join("|") + ")\\b" : "(" + escapedPatterns.join("|") + ")";
            return caseSensitive ? new RegExp(regexStr) : new RegExp(regexStr, "i");
        }
    }(window.document);
    var Input = function() {
        var specialKeyCodeMap;
        specialKeyCodeMap = {
            9: "tab",
            27: "esc",
            37: "left",
            39: "right",
            13: "enter",
            38: "up",
            40: "down"
        };
        function Input(o) {
            var that = this, onBlur, onFocus, onKeydown, onInput;
            o = o || {};
            if (!o.input) {
                $.error("input is missing");
            }
            onBlur = _.bind(this._onBlur, this);
            onFocus = _.bind(this._onFocus, this);
            onKeydown = _.bind(this._onKeydown, this);
            onInput = _.bind(this._onInput, this);
            this.$hint = $(o.hint);
            this.$input = $(o.input).on("blur.tt", onBlur).on("focus.tt", onFocus).on("keydown.tt", onKeydown);
            if (this.$hint.length === 0) {
                this.setHint = this.getHint = this.clearHint = this.clearHintIfInvalid = _.noop;
            }
            if (!_.isMsie()) {
                this.$input.on("input.tt", onInput);
            } else {
                this.$input.on("keydown.tt keypress.tt cut.tt paste.tt", function($e) {
                    if (specialKeyCodeMap[$e.which || $e.keyCode]) {
                        return;
                    }
                    _.defer(_.bind(that._onInput, that, $e));
                });
            }
            this.query = this.$input.val();
            this.$overflowHelper = buildOverflowHelper(this.$input);
        }
        Input.normalizeQuery = function(str) {
            return (str || "").replace(/^\s*/g, "").replace(/\s{2,}/g, " ");
        };
        _.mixin(Input.prototype, EventEmitter, {
            _onBlur: function onBlur() {
                this.resetInputValue();
                this.trigger("blurred");
            },
            _onFocus: function onFocus() {
                this.trigger("focused");
            },
            _onKeydown: function onKeydown($e) {
                var keyName = specialKeyCodeMap[$e.which || $e.keyCode];
                this._managePreventDefault(keyName, $e);
                if (keyName && this._shouldTrigger(keyName, $e)) {
                    this.trigger(keyName + "Keyed", $e);
                }
            },
            _onInput: function onInput() {
                this._checkInputValue();
            },
            _managePreventDefault: function managePreventDefault(keyName, $e) {
                var preventDefault, hintValue, inputValue;
                switch (keyName) {
                  case "tab":
                    hintValue = this.getHint();
                    inputValue = this.getInputValue();
                    preventDefault = hintValue && hintValue !== inputValue && !withModifier($e);
                    break;

                  case "up":
                  case "down":
                    preventDefault = !withModifier($e);
                    break;

                  default:
                    preventDefault = false;
                }
                preventDefault && $e.preventDefault();
            },
            _shouldTrigger: function shouldTrigger(keyName, $e) {
                var trigger;
                switch (keyName) {
                  case "tab":
                    trigger = !withModifier($e);
                    break;

                  default:
                    trigger = true;
                }
                return trigger;
            },
            _checkInputValue: function checkInputValue() {
                var inputValue, areEquivalent, hasDifferentWhitespace;
                inputValue = this.getInputValue();
                areEquivalent = areQueriesEquivalent(inputValue, this.query);
                hasDifferentWhitespace = areEquivalent ? this.query.length !== inputValue.length : false;
                if (!areEquivalent) {
                    this.trigger("queryChanged", this.query = inputValue);
                } else if (hasDifferentWhitespace) {
                    this.trigger("whitespaceChanged", this.query);
                }
            },
            focus: function focus() {
                this.$input.focus();
            },
            blur: function blur() {
                this.$input.blur();
            },
            getQuery: function getQuery() {
                return this.query;
            },
            setQuery: function setQuery(query) {
                this.query = query;
            },
            getInputValue: function getInputValue() {
                return this.$input.val();
            },
            setInputValue: function setInputValue(value, silent) {
                this.$input.val(value);
                silent ? this.clearHint() : this._checkInputValue();
            },
            resetInputValue: function resetInputValue() {
                this.setInputValue(this.query, true);
            },
            getHint: function getHint() {
                return this.$hint.val();
            },
            setHint: function setHint(value) {
                this.$hint.val(value);
            },
            clearHint: function clearHint() {
                this.setHint("");
            },
            clearHintIfInvalid: function clearHintIfInvalid() {
                var val, hint, valIsPrefixOfHint, isValid;
                val = this.getInputValue();
                hint = this.getHint();
                valIsPrefixOfHint = val !== hint && hint.indexOf(val) === 0;
                isValid = val !== "" && valIsPrefixOfHint && !this.hasOverflow();
                !isValid && this.clearHint();
            },
            getLanguageDirection: function getLanguageDirection() {
                return (this.$input.css("direction") || "ltr").toLowerCase();
            },
            hasOverflow: function hasOverflow() {
                var constraint = this.$input.width() - 2;
                this.$overflowHelper.text(this.getInputValue());
                return this.$overflowHelper.width() >= constraint;
            },
            isCursorAtEnd: function() {
                var valueLength, selectionStart, range;
                valueLength = this.$input.val().length;
                selectionStart = this.$input[0].selectionStart;
                if (_.isNumber(selectionStart)) {
                    return selectionStart === valueLength;
                } else if (document.selection) {
                    range = document.selection.createRange();
                    range.moveStart("character", -valueLength);
                    return valueLength === range.text.length;
                }
                return true;
            },
            destroy: function destroy() {
                this.$hint.off(".tt");
                this.$input.off(".tt");
                this.$hint = this.$input = this.$overflowHelper = null;
            }
        });
        return Input;
        function buildOverflowHelper($input) {
            return $('<pre aria-hidden="true"></pre>').css({
                position: "absolute",
                visibility: "hidden",
                whiteSpace: "pre",
                fontFamily: $input.css("font-family"),
                fontSize: $input.css("font-size"),
                fontStyle: $input.css("font-style"),
                fontVariant: $input.css("font-variant"),
                fontWeight: $input.css("font-weight"),
                wordSpacing: $input.css("word-spacing"),
                letterSpacing: $input.css("letter-spacing"),
                textIndent: $input.css("text-indent"),
                textRendering: $input.css("text-rendering"),
                textTransform: $input.css("text-transform")
            }).insertAfter($input);
        }
        function areQueriesEquivalent(a, b) {
            return Input.normalizeQuery(a) === Input.normalizeQuery(b);
        }
        function withModifier($e) {
            return $e.altKey || $e.ctrlKey || $e.metaKey || $e.shiftKey;
        }
    }();
    var Dataset = function() {
        var datasetKey = "ttDataset", valueKey = "ttValue", datumKey = "ttDatum";
        function Dataset(o) {
            o = o || {};
            o.templates = o.templates || {};
            if (!o.source) {
                $.error("missing source");
            }
            if (o.name && !isValidName(o.name)) {
                $.error("invalid dataset name: " + o.name);
            }
            this.query = null;
            this.highlight = !!o.highlight;
            this.name = o.name || _.getUniqueId();
            this.source = o.source;
            this.displayFn = getDisplayFn(o.display || o.displayKey);
            this.templates = getTemplates(o.templates, this.displayFn);
            this.$el = $(html.dataset.replace("%CLASS%", this.name));
        }
        Dataset.extractDatasetName = function extractDatasetName(el) {
            return $(el).data(datasetKey);
        };
        Dataset.extractValue = function extractDatum(el) {
            return $(el).data(valueKey);
        };
        Dataset.extractDatum = function extractDatum(el) {
            return $(el).data(datumKey);
        };
        _.mixin(Dataset.prototype, EventEmitter, {
            _render: function render(query, suggestions) {
                if (!this.$el) {
                    return;
                }
                var that = this, hasSuggestions;
                this.$el.empty();
                hasSuggestions = suggestions && suggestions.length;
                if (!hasSuggestions && this.templates.empty) {
                    this.$el.html(getEmptyHtml()).prepend(that.templates.header ? getHeaderHtml() : null).append(that.templates.footer ? getFooterHtml() : null);
                } else if (hasSuggestions) {
                    this.$el.html(getSuggestionsHtml()).prepend(that.templates.header ? getHeaderHtml() : null).append(that.templates.footer ? getFooterHtml() : null);
                }
                this.trigger("rendered");
                function getEmptyHtml() {
                    return that.templates.empty({
                        query: query,
                        isEmpty: true
                    });
                }
                function getSuggestionsHtml() {
                    var $suggestions, nodes;
                    $suggestions = $(html.suggestions).css(css.suggestions);
                    nodes = _.map(suggestions, getSuggestionNode);
                    $suggestions.append.apply($suggestions, nodes);
                    that.highlight && highlight({
                        node: $suggestions[0],
                        pattern: query
                    });
                    return $suggestions;
                    function getSuggestionNode(suggestion) {
                        var $el;
                        $el = $(html.suggestion).append(that.templates.suggestion(suggestion)).data(datasetKey, that.name).data(valueKey, that.displayFn(suggestion)).data(datumKey, suggestion);
                        $el.children().each(function() {
                            $(this).css(css.suggestionChild);
                        });
                        return $el;
                    }
                }
                function getHeaderHtml() {
                    return that.templates.header({
                        query: query,
                        isEmpty: !hasSuggestions
                    });
                }
                function getFooterHtml() {
                    return that.templates.footer({
                        query: query,
                        isEmpty: !hasSuggestions
                    });
                }
            },
            getRoot: function getRoot() {
                return this.$el;
            },
            update: function update(query) {
                var that = this;
                this.query = query;
                this.canceled = false;
                this.source(query, render);
                function render(suggestions) {
                    if (!that.canceled && query === that.query) {
                        that._render(query, suggestions);
                    }
                }
            },
            cancel: function cancel() {
                this.canceled = true;
            },
            clear: function clear() {
                this.cancel();
                this.$el.empty();
                this.trigger("rendered");
            },
            isEmpty: function isEmpty() {
                return this.$el.is(":empty");
            },
            destroy: function destroy() {
                this.$el = null;
            }
        });
        return Dataset;
        function getDisplayFn(display) {
            display = display || "value";
            return _.isFunction(display) ? display : displayFn;
            function displayFn(obj) {
                return obj[display];
            }
        }
        function getTemplates(templates, displayFn) {
            return {
                empty: templates.empty && _.templatify(templates.empty),
                header: templates.header && _.templatify(templates.header),
                footer: templates.footer && _.templatify(templates.footer),
                suggestion: templates.suggestion || suggestionTemplate
            };
            function suggestionTemplate(context) {
                return "<p>" + displayFn(context) + "</p>";
            }
        }
        function isValidName(str) {
            return /^[_a-zA-Z0-9-]+$/.test(str);
        }
    }();
    var Dropdown = function() {
        function Dropdown(o) {
            var that = this, onSuggestionClick, onSuggestionMouseEnter, onSuggestionMouseLeave;
            o = o || {};
            if (!o.menu) {
                $.error("menu is required");
            }
            this.isOpen = false;
            this.isEmpty = true;
            this.datasets = _.map(o.datasets, initializeDataset);
            onSuggestionClick = _.bind(this._onSuggestionClick, this);
            onSuggestionMouseEnter = _.bind(this._onSuggestionMouseEnter, this);
            onSuggestionMouseLeave = _.bind(this._onSuggestionMouseLeave, this);
            this.$menu = $(o.menu).on("click.tt", ".tt-suggestion", onSuggestionClick).on("mouseenter.tt", ".tt-suggestion", onSuggestionMouseEnter).on("mouseleave.tt", ".tt-suggestion", onSuggestionMouseLeave);
            _.each(this.datasets, function(dataset) {
                that.$menu.append(dataset.getRoot());
                dataset.onSync("rendered", that._onRendered, that);
            });
        }
        _.mixin(Dropdown.prototype, EventEmitter, {
            _onSuggestionClick: function onSuggestionClick($e) {
                this.trigger("suggestionClicked", $($e.currentTarget));
            },
            _onSuggestionMouseEnter: function onSuggestionMouseEnter($e) {
                this._removeCursor();
                this._setCursor($($e.currentTarget), true);
            },
            _onSuggestionMouseLeave: function onSuggestionMouseLeave() {
                this._removeCursor();
            },
            _onRendered: function onRendered() {
                this.isEmpty = _.every(this.datasets, isDatasetEmpty);
                this.isEmpty ? this._hide() : this.isOpen && this._show();
                this.trigger("datasetRendered");
                function isDatasetEmpty(dataset) {
                    return dataset.isEmpty();
                }
            },
            _hide: function() {
                this.$menu.hide();
            },
            _show: function() {
                this.$menu.css("display", "block");
            },
            _getSuggestions: function getSuggestions() {
                return this.$menu.find(".tt-suggestion");
            },
            _getCursor: function getCursor() {
                return this.$menu.find(".tt-cursor").first();
            },
            _setCursor: function setCursor($el, silent) {
                $el.first().addClass("tt-cursor");
                !silent && this.trigger("cursorMoved");
            },
            _removeCursor: function removeCursor() {
                this._getCursor().removeClass("tt-cursor");
            },
            _moveCursor: function moveCursor(increment) {
                var $suggestions, $oldCursor, newCursorIndex, $newCursor;
                if (!this.isOpen) {
                    return;
                }
                $oldCursor = this._getCursor();
                $suggestions = this._getSuggestions();
                this._removeCursor();
                newCursorIndex = $suggestions.index($oldCursor) + increment;
                newCursorIndex = (newCursorIndex + 1) % ($suggestions.length + 1) - 1;
                if (newCursorIndex === -1) {
                    this.trigger("cursorRemoved");
                    return;
                } else if (newCursorIndex < -1) {
                    newCursorIndex = $suggestions.length - 1;
                }
                this._setCursor($newCursor = $suggestions.eq(newCursorIndex));
                this._ensureVisible($newCursor);
            },
            _ensureVisible: function ensureVisible($el) {
                var elTop, elBottom, menuScrollTop, menuHeight;
                elTop = $el.position().top;
                elBottom = elTop + $el.outerHeight(true);
                menuScrollTop = this.$menu.scrollTop();
                menuHeight = this.$menu.height() + parseInt(this.$menu.css("paddingTop"), 10) + parseInt(this.$menu.css("paddingBottom"), 10);
                if (elTop < 0) {
                    this.$menu.scrollTop(menuScrollTop + elTop);
                } else if (menuHeight < elBottom) {
                    this.$menu.scrollTop(menuScrollTop + (elBottom - menuHeight));
                }
            },
            close: function close() {
                if (this.isOpen) {
                    this.isOpen = false;
                    this._removeCursor();
                    this._hide();
                    this.trigger("closed");
                }
            },
            open: function open() {
                if (!this.isOpen) {
                    this.isOpen = true;
                    !this.isEmpty && this._show();
                    this.trigger("opened");
                }
            },
            setLanguageDirection: function setLanguageDirection(dir) {
                this.$menu.css(dir === "ltr" ? css.ltr : css.rtl);
            },
            moveCursorUp: function moveCursorUp() {
                this._moveCursor(-1);
            },
            moveCursorDown: function moveCursorDown() {
                this._moveCursor(+1);
            },
            getDatumForSuggestion: function getDatumForSuggestion($el) {
                var datum = null;
                if ($el.length) {
                    datum = {
                        raw: Dataset.extractDatum($el),
                        value: Dataset.extractValue($el),
                        datasetName: Dataset.extractDatasetName($el)
                    };
                }
                return datum;
            },
            getDatumForCursor: function getDatumForCursor() {
                return this.getDatumForSuggestion(this._getCursor().first());
            },
            getDatumForTopSuggestion: function getDatumForTopSuggestion() {
                return this.getDatumForSuggestion(this._getSuggestions().first());
            },
            update: function update(query) {
                _.each(this.datasets, updateDataset);
                function updateDataset(dataset) {
                    dataset.update(query);
                }
            },
            empty: function empty() {
                _.each(this.datasets, clearDataset);
                this.isEmpty = true;
                function clearDataset(dataset) {
                    dataset.clear();
                }
            },
            isVisible: function isVisible() {
                return this.isOpen && !this.isEmpty;
            },
            destroy: function destroy() {
                this.$menu.off(".tt");
                this.$menu = null;
                _.each(this.datasets, destroyDataset);
                function destroyDataset(dataset) {
                    dataset.destroy();
                }
            }
        });
        return Dropdown;
        function initializeDataset(oDataset) {
            return new Dataset(oDataset);
        }
    }();
    var Typeahead = function() {
        var attrsKey = "ttAttrs";
        function Typeahead(o) {
            var $menu, $input, $hint;
            o = o || {};
            if (!o.input) {
                $.error("missing input");
            }
            this.isActivated = false;
            this.autoselect = !!o.autoselect;
            this.minLength = _.isNumber(o.minLength) ? o.minLength : 1;
            this.$node = buildDomStructure(o.input, o.withHint);
            $menu = this.$node.find(".tt-dropdown-menu");
            $input = this.$node.find(".tt-input");
            $hint = this.$node.find(".tt-hint");
            $input.on("blur.tt", function($e) {
                var active, isActive, hasActive;
                active = document.activeElement;
                isActive = $menu.is(active);
                hasActive = $menu.has(active).length > 0;
                if (_.isMsie() && (isActive || hasActive)) {
                    $e.preventDefault();
                    $e.stopImmediatePropagation();
                    _.defer(function() {
                        $input.focus();
                    });
                }
            });
            $menu.on("mousedown.tt", function($e) {
                $e.preventDefault();
            });
            this.eventBus = o.eventBus || new EventBus({
                el: $input
            });
            this.dropdown = new Dropdown({
                menu: $menu,
                datasets: o.datasets
            }).onSync("suggestionClicked", this._onSuggestionClicked, this).onSync("cursorMoved", this._onCursorMoved, this).onSync("cursorRemoved", this._onCursorRemoved, this).onSync("opened", this._onOpened, this).onSync("closed", this._onClosed, this).onAsync("datasetRendered", this._onDatasetRendered, this);
            this.input = new Input({
                input: $input,
                hint: $hint
            }).onSync("focused", this._onFocused, this).onSync("blurred", this._onBlurred, this).onSync("enterKeyed", this._onEnterKeyed, this).onSync("tabKeyed", this._onTabKeyed, this).onSync("escKeyed", this._onEscKeyed, this).onSync("upKeyed", this._onUpKeyed, this).onSync("downKeyed", this._onDownKeyed, this).onSync("leftKeyed", this._onLeftKeyed, this).onSync("rightKeyed", this._onRightKeyed, this).onSync("queryChanged", this._onQueryChanged, this).onSync("whitespaceChanged", this._onWhitespaceChanged, this);
            this._setLanguageDirection();
        }
        _.mixin(Typeahead.prototype, {
            _onSuggestionClicked: function onSuggestionClicked(type, $el) {
                var datum;
                if (datum = this.dropdown.getDatumForSuggestion($el)) {
                    this._select(datum);
                }
            },
            _onCursorMoved: function onCursorMoved() {
                var datum = this.dropdown.getDatumForCursor();
                this.input.setInputValue(datum.value, true);
                this.eventBus.trigger("cursorchanged", datum.raw, datum.datasetName);
            },
            _onCursorRemoved: function onCursorRemoved() {
                this.input.resetInputValue();
                this._updateHint();
            },
            _onDatasetRendered: function onDatasetRendered() {
                this._updateHint();
            },
            _onOpened: function onOpened() {
                this._updateHint();
                this.eventBus.trigger("opened");
            },
            _onClosed: function onClosed() {
                this.input.clearHint();
                this.eventBus.trigger("closed");
            },
            _onFocused: function onFocused() {
                this.isActivated = true;
                this.dropdown.open();
            },
            _onBlurred: function onBlurred() {
                this.isActivated = false;
                this.dropdown.empty();
                this.dropdown.close();
            },
            _onEnterKeyed: function onEnterKeyed(type, $e) {
                var cursorDatum, topSuggestionDatum;
                cursorDatum = this.dropdown.getDatumForCursor();
                topSuggestionDatum = this.dropdown.getDatumForTopSuggestion();
                if (cursorDatum) {
                    this._select(cursorDatum);
                    $e.preventDefault();
                } else if (this.autoselect && topSuggestionDatum) {
                    this._select(topSuggestionDatum);
                    $e.preventDefault();
                }
            },
            _onTabKeyed: function onTabKeyed(type, $e) {
                var datum;
                if (datum = this.dropdown.getDatumForCursor()) {
                    this._select(datum);
                    $e.preventDefault();
                } else {
                    this._autocomplete(true);
                }
            },
            _onEscKeyed: function onEscKeyed() {
                this.dropdown.close();
                this.input.resetInputValue();
            },
            _onUpKeyed: function onUpKeyed() {
                var query = this.input.getQuery();
                this.dropdown.isEmpty && query.length >= this.minLength ? this.dropdown.update(query) : this.dropdown.moveCursorUp();
                this.dropdown.open();
            },
            _onDownKeyed: function onDownKeyed() {
                var query = this.input.getQuery();
                this.dropdown.isEmpty && query.length >= this.minLength ? this.dropdown.update(query) : this.dropdown.moveCursorDown();
                this.dropdown.open();
            },
            _onLeftKeyed: function onLeftKeyed() {
                this.dir === "rtl" && this._autocomplete();
            },
            _onRightKeyed: function onRightKeyed() {
                this.dir === "ltr" && this._autocomplete();
            },
            _onQueryChanged: function onQueryChanged(e, query) {
                this.input.clearHintIfInvalid();
                query.length >= this.minLength ? this.dropdown.update(query) : this.dropdown.empty();
                this.dropdown.open();
                this._setLanguageDirection();
            },
            _onWhitespaceChanged: function onWhitespaceChanged() {
                this._updateHint();
                this.dropdown.open();
            },
            _setLanguageDirection: function setLanguageDirection() {
                var dir;
                if (this.dir !== (dir = this.input.getLanguageDirection())) {
                    this.dir = dir;
                    this.$node.css("direction", dir);
                    this.dropdown.setLanguageDirection(dir);
                }
            },
            _updateHint: function updateHint() {
                var datum, val, query, escapedQuery, frontMatchRegEx, match;
                datum = this.dropdown.getDatumForTopSuggestion();
                if (datum && this.dropdown.isVisible() && !this.input.hasOverflow()) {
                    val = this.input.getInputValue();
                    query = Input.normalizeQuery(val);
                    escapedQuery = _.escapeRegExChars(query);
                    frontMatchRegEx = new RegExp("^(?:" + escapedQuery + ")(.+$)", "i");
                    match = frontMatchRegEx.exec(datum.value);
                    match ? this.input.setHint(val + match[1]) : this.input.clearHint();
                } else {
                    this.input.clearHint();
                }
            },
            _autocomplete: function autocomplete(laxCursor) {
                var hint, query, isCursorAtEnd, datum;
                hint = this.input.getHint();
                query = this.input.getQuery();
                isCursorAtEnd = laxCursor || this.input.isCursorAtEnd();
                if (hint && query !== hint && isCursorAtEnd) {
                    datum = this.dropdown.getDatumForTopSuggestion();
                    datum && this.input.setInputValue(datum.value);
                    this.eventBus.trigger("autocompleted", datum.raw, datum.datasetName);
                }
            },
            _select: function select(datum) {
                this.input.setQuery(datum.value);
                this.input.setInputValue(datum.value, true);
                this._setLanguageDirection();
                this.eventBus.trigger("selected", datum.raw, datum.datasetName);
                this.dropdown.close();
                _.defer(_.bind(this.dropdown.empty, this.dropdown));
            },
            open: function open() {
                this.dropdown.open();
            },
            close: function close() {
                this.dropdown.close();
            },
            setVal: function setVal(val) {
                if (this.isActivated) {
                    this.input.setInputValue(val);
                } else {
                    this.input.setQuery(val);
                    this.input.setInputValue(val, true);
                }
                this._setLanguageDirection();
            },
            getVal: function getVal() {
                return this.input.getQuery();
            },
            destroy: function destroy() {
                this.input.destroy();
                this.dropdown.destroy();
                destroyDomStructure(this.$node);
                this.$node = null;
            }
        });
        return Typeahead;
        function buildDomStructure(input, withHint) {
            var $input, $wrapper, $dropdown, $hint;
            $input = $(input);
            $wrapper = $(html.wrapper).css(css.wrapper);
            $dropdown = $(html.dropdown).css(css.dropdown);
            $hint = $input.clone().css(css.hint).css(getBackgroundStyles($input));
            $hint.val("").removeData().addClass("tt-hint").removeAttr("id name placeholder").prop("disabled", true).attr({
                autocomplete: "off",
                spellcheck: "false"
            });
            $input.data(attrsKey, {
                dir: $input.attr("dir"),
                autocomplete: $input.attr("autocomplete"),
                spellcheck: $input.attr("spellcheck"),
                style: $input.attr("style")
            });
            $input.addClass("tt-input").attr({
                autocomplete: "off",
                spellcheck: false
            }).css(withHint ? css.input : css.inputWithNoHint);
            try {
                !$input.attr("dir") && $input.attr("dir", "auto");
            } catch (e) {}
            return $input.wrap($wrapper).parent().prepend(withHint ? $hint : null).append($dropdown);
        }
        function getBackgroundStyles($el) {
            return {
                backgroundAttachment: $el.css("background-attachment"),
                backgroundClip: $el.css("background-clip"),
                backgroundColor: $el.css("background-color"),
                backgroundImage: $el.css("background-image"),
                backgroundOrigin: $el.css("background-origin"),
                backgroundPosition: $el.css("background-position"),
                backgroundRepeat: $el.css("background-repeat"),
                backgroundSize: $el.css("background-size")
            };
        }
        function destroyDomStructure($node) {
            var $input = $node.find(".tt-input");
            _.each($input.data(attrsKey), function(val, key) {
                _.isUndefined(val) ? $input.removeAttr(key) : $input.attr(key, val);
            });
            $input.detach().removeData(attrsKey).removeClass("tt-input").insertAfter($node);
            $node.remove();
        }
    }();
    (function() {
        var old, typeaheadKey, methods;
        old = $.fn.typeahead;
        typeaheadKey = "ttTypeahead";
        methods = {
            initialize: function initialize(o, datasets) {
                datasets = _.isArray(datasets) ? datasets : [].slice.call(arguments, 1);
                o = o || {};
                return this.each(attach);
                function attach() {
                    var $input = $(this), eventBus, typeahead;
                    _.each(datasets, function(d) {
                        d.highlight = !!o.highlight;
                    });
                    typeahead = new Typeahead({
                        input: $input,
                        eventBus: eventBus = new EventBus({
                            el: $input
                        }),
                        withHint: _.isUndefined(o.hint) ? true : !!o.hint,
                        minLength: o.minLength,
                        autoselect: o.autoselect,
                        datasets: datasets
                    });
                    $input.data(typeaheadKey, typeahead);
                }
            },
            open: function open() {
                return this.each(openTypeahead);
                function openTypeahead() {
                    var $input = $(this), typeahead;
                    if (typeahead = $input.data(typeaheadKey)) {
                        typeahead.open();
                    }
                }
            },
            close: function close() {
                return this.each(closeTypeahead);
                function closeTypeahead() {
                    var $input = $(this), typeahead;
                    if (typeahead = $input.data(typeaheadKey)) {
                        typeahead.close();
                    }
                }
            },
            val: function val(newVal) {
                return !arguments.length ? getVal(this.first()) : this.each(setVal);
                function setVal() {
                    var $input = $(this), typeahead;
                    if (typeahead = $input.data(typeaheadKey)) {
                        typeahead.setVal(newVal);
                    }
                }
                function getVal($input) {
                    var typeahead, query;
                    if (typeahead = $input.data(typeaheadKey)) {
                        query = typeahead.getVal();
                    }
                    return query;
                }
            },
            destroy: function destroy() {
                return this.each(unattach);
                function unattach() {
                    var $input = $(this), typeahead;
                    if (typeahead = $input.data(typeaheadKey)) {
                        typeahead.destroy();
                        $input.removeData(typeaheadKey);
                    }
                }
            }
        };
        $.fn.typeahead = function(method) {
            if (methods[method]) {
                return methods[method].apply(this, [].slice.call(arguments, 1));
            } else {
                return methods.initialize.apply(this, arguments);
            }
        };
        $.fn.typeahead.noConflict = function noConflict() {
            $.fn.typeahead = old;
            return this;
        };
    })();
})(window.jQuery);
var ADDRESS = [{"cities": [{"regions": [{"regionName": "谯城"}, {"regionName": "利辛"}, {"regionName": "蒙城"}, {"regionName": "涡阳"}], "cityName": "亳州"}, {"regions": [{"regionName": "枞阳"}, {"regionName": "大观"}, {"regionName": "怀宁"}, {"regionName": "潜山"}, {"regionName": "太湖"}, {"regionName": "宿松"}, {"regionName": "桐城"}, {"regionName": "望江"}, {"regionName": "迎江"}, {"regionName": "岳西"}, {"regionName": "宜秀"}], "cityName": "安庆"}, {"regions": [{"regionName": "蚌山"}, {"regionName": "固镇"}, {"regionName": "淮上"}, {"regionName": "怀远"}, {"regionName": "龙子湖"}, {"regionName": "五河"}, {"regionName": "禹会"}], "cityName": "蚌埠"}, {"regions": [{"regionName": "含山"}, {"regionName": "和县"}, {"regionName": "居巢"}, {"regionName": "庐江"}, {"regionName": "无为"}], "cityName": "巢湖"}, {"regions": [{"regionName": "定远"}, {"regionName": "凤阳"}, {"regionName": "琅琊"}, {"regionName": "来安"}, {"regionName": "明光"}, {"regionName": "南谯"}, {"regionName": "全椒"}, {"regionName": "天长"}], "cityName": "滁州"}, {"regions": [{"regionName": "东至"}, {"regionName": "贵池"}, {"regionName": "青阳"}, {"regionName": "石台"}], "cityName": "池州"}, {"regions": [{"regionName": "颍东"}, {"regionName": "颍东经济开发区"}, {"regionName": "颍泉"}, {"regionName": "颍泉经济开发区"}, {"regionName": "颍上"}, {"regionName": "颍州"}, {"regionName": "颍州经济开发区"}, {"regionName": "阜南"}, {"regionName": "界首"}, {"regionName": "临泉"}, {"regionName": "太和"}], "cityName": "阜阳"}, {"regions": [{"regionName": "濉溪"}, {"regionName": "杜集"}, {"regionName": "烈山"}, {"regionName": "相山"}], "cityName": "淮北"}, {"regions": [{"regionName": "滨湖"}, {"regionName": "包河"}, {"regionName": "长丰"}, {"regionName": "肥东"}, {"regionName": "肥西"}, {"regionName": "高新"}, {"regionName": "经开"}, {"regionName": "庐阳"}, {"regionName": "蜀山"}, {"regionName": "新站"}, {"regionName": "瑶海"}, {"regionName": "政务"}], "cityName": "合肥"}, {"regions": [{"regionName": "八公山"}, {"regionName": "大通"}, {"regionName": "凤台"}, {"regionName": "潘集"}, {"regionName": "田家庵"}, {"regionName": "谢家集"}], "cityName": "淮南"}, {"regions": [{"regionName": "黟县"}, {"regionName": "歙县"}, {"regionName": "黄山区"}, {"regionName": "徽州"}, {"regionName": "祁门"}, {"regionName": "屯溪"}, {"regionName": "休宁"}], "cityName": "黄山"}, {"regions": [{"regionName": "霍邱"}, {"regionName": "霍山"}, {"regionName": "金安"}, {"regionName": "金寨"}, {"regionName": "舒城"}, {"regionName": "寿县"}, {"regionName": "裕安"}], "cityName": "六安"}, {"regions": [{"regionName": "当涂"}, {"regionName": "花山"}, {"regionName": "金家庄"}, {"regionName": "雨山"}], "cityName": "马鞍山"}, {"regions": [{"regionName": "埇桥"}, {"regionName": "砀山"}, {"regionName": "泗县"}, {"regionName": "灵璧"}, {"regionName": "萧县"}], "cityName": "宿州"}, {"regions": [{"regionName": "郊区"}, {"regionName": "狮子山"}, {"regionName": "铜官山"}, {"regionName": "铜陵县"}], "cityName": "铜陵"}, {"regions": [{"regionName": "弋江"}, {"regionName": "鸠江"}, {"regionName": "繁昌"}, {"regionName": "镜湖"}, {"regionName": "南陵"}, {"regionName": "三山"}, {"regionName": "芜湖县"}, {"regionName": "无为"}], "cityName": "芜湖"}, {"regions": [{"regionName": "旌德"}, {"regionName": "泾县"}, {"regionName": "广德"}, {"regionName": "绩溪"}, {"regionName": "郎溪"}, {"regionName": "宁国"}, {"regionName": "宣州"}], "cityName": "宣城"}], "provName": "安徽"}, {"cities": [{"regions": [], "cityName": "北京周边"}, {"regions": [], "cityName": "昌平"}, {"regions": [], "cityName": "崇文"}, {"regions": [], "cityName": "朝阳"}, {"regions": [], "cityName": "东城"}, {"regions": [], "cityName": "大兴"}, {"regions": [], "cityName": "丰台"}, {"regions": [], "cityName": "房山"}, {"regions": [], "cityName": "海淀"}, {"regions": [], "cityName": "怀柔"}, {"regions": [], "cityName": "门头沟"}, {"regions": [], "cityName": "密云"}, {"regions": [], "cityName": "平谷"}, {"regions": [], "cityName": "石景山"}, {"regions": [], "cityName": "顺义"}, {"regions": [], "cityName": "通州"}, {"regions": [], "cityName": "西城"}, {"regions": [], "cityName": "宣武"}, {"regions": [], "cityName": "燕郊"}, {"regions": [], "cityName": "延庆"}], "provName": "北京"}, {"cities": [{"regions": [{"regionName": "长乐"}, {"regionName": "仓山"}, {"regionName": "福清"}, {"regionName": "鼓楼"}, {"regionName": "晋安"}, {"regionName": "连江"}, {"regionName": "罗源"}, {"regionName": "闽侯"}, {"regionName": "闽清"}, {"regionName": "马尾"}, {"regionName": "平潭"}, {"regionName": "其他"}, {"regionName": "台江"}, {"regionName": "永泰"}], "cityName": "福州"}, {"regions": [{"regionName": "长汀"}, {"regionName": "连城"}, {"regionName": "上杭"}, {"regionName": "武平"}, {"regionName": "新罗"}, {"regionName": "永定"}, {"regionName": "漳平"}], "cityName": "龙岩"}, {"regions": [{"regionName": "柘荣"}, {"regionName": "福安"}, {"regionName": "福鼎"}, {"regionName": "古田"}, {"regionName": "蕉城"}, {"regionName": "屏南"}, {"regionName": "寿宁"}, {"regionName": "霞浦"}, {"regionName": "周宁"}], "cityName": "宁德"}, {"regions": [{"regionName": "光泽"}, {"regionName": "建瓯"}, {"regionName": "建阳"}, {"regionName": "浦城"}, {"regionName": "顺昌"}, {"regionName": "邵武"}, {"regionName": "松溪"}, {"regionName": "武夷山"}, {"regionName": "延平"}, {"regionName": "政和"}], "cityName": "南平"}, {"regions": [{"regionName": "城厢"}, {"regionName": "涵江"}, {"regionName": "荔城"}, {"regionName": "仙游"}, {"regionName": "秀屿"}], "cityName": "莆田"}, {"regions": [{"regionName": "安溪"}, {"regionName": "德化"}, {"regionName": "丰泽"}, {"regionName": "惠安"}, {"regionName": "晋江"}, {"regionName": "金门"}, {"regionName": "鲤城"}, {"regionName": "洛江"}, {"regionName": "南安"}, {"regionName": "泉港"}, {"regionName": "石狮"}, {"regionName": "永春"}], "cityName": "泉州"}, {"regions": [{"regionName": "大田"}, {"regionName": "将乐"}, {"regionName": "建宁"}, {"regionName": "梅列"}, {"regionName": "明溪"}, {"regionName": "宁化"}, {"regionName": "清流"}, {"regionName": "泰宁"}, {"regionName": "沙县"}, {"regionName": "三元"}, {"regionName": "永安"}, {"regionName": "尤溪"}], "cityName": "三明"}, {"regions": [{"regionName": "海沧"}, {"regionName": "湖里"}, {"regionName": "集美"}, {"regionName": "思明"}, {"regionName": "同安"}, {"regionName": "翔安"}, {"regionName": "厦门周边"}], "cityName": "厦门"}, {"regions": [{"regionName": "诏安"}, {"regionName": "芗城"}, {"regionName": "长泰"}, {"regionName": "东山"}, {"regionName": "华安"}, {"regionName": "龙海"}, {"regionName": "龙文"}, {"regionName": "南靖"}, {"regionName": "平和"}, {"regionName": "云霄"}, {"regionName": "漳浦"}], "cityName": "漳州"}], "provName": "福建"}, {"cities": [{"regions": [{"regionName": "潮安"}, {"regionName": "饶平"}, {"regionName": "湘桥"}], "cityName": "潮州"}, {"regions": [{"regionName": "寮步"}, {"regionName": "莞城"}, {"regionName": "长安"}, {"regionName": "常平"}, {"regionName": "茶山"}, {"regionName": "道滘"}, {"regionName": "东城"}, {"regionName": "东坑"}, {"regionName": "大朗"}, {"regionName": "大岭山"}, {"regionName": "凤岗"}, {"regionName": "高埗"}, {"regionName": "黄江"}, {"regionName": "厚街"}, {"regionName": "横沥"}, {"regionName": "虎门"}, {"regionName": "洪梅"}, {"regionName": "麻涌"}, {"regionName": "南城"}, {"regionName": "企石"}, {"regionName": "桥头"}, {"regionName": "清溪"}, {"regionName": "石碣"}, {"regionName": "石龙"}, {"regionName": "石排"}, {"regionName": "松山湖"}, {"regionName": "沙田"}, {"regionName": "塘厦"}, {"regionName": "万江"}, {"regionName": "望牛墩"}, {"regionName": "谢岗"}, {"regionName": "樟木头"}, {"regionName": "中堂"}], "cityName": "东莞"}, {"regions": [{"regionName": "禅城"}, {"regionName": "高明"}, {"regionName": "南海"}, {"regionName": "顺德"}, {"regionName": "三水"}], "cityName": "佛山"}, {"regions": [{"regionName": "白云"}, {"regionName": "从化"}, {"regionName": "番禺"}, {"regionName": "花都"}, {"regionName": "黄埔"}, {"regionName": "海珠"}, {"regionName": "经济开发区"}, {"regionName": "萝岗"}, {"regionName": "荔湾"}, {"regionName": "南沙"}, {"regionName": "天河"}, {"regionName": "越秀"}, {"regionName": "增城"}], "cityName": "广州"}, {"regions": [{"regionName": "东源"}, {"regionName": "和平"}, {"regionName": "龙川"}, {"regionName": "连平"}, {"regionName": "源城"}, {"regionName": "紫金"}], "cityName": "河源"}, {"regions": [{"regionName": "博罗"}, {"regionName": "大亚湾区"}, {"regionName": "惠城"}, {"regionName": "惠东"}, {"regionName": "惠阳"}, {"regionName": "惠州周边"}, {"regionName": "龙门"}, {"regionName": "仲恺区"}], "cityName": "惠州"}, {"regions": [{"regionName": "恩平"}, {"regionName": "鹤山"}, {"regionName": "江海"}, {"regionName": "开平"}, {"regionName": "蓬江"}, {"regionName": "台山"}, {"regionName": "新会"}], "cityName": "江门"}, {"regions": [{"regionName": "榕城"}, {"regionName": "惠来"}, {"regionName": "揭东"}, {"regionName": "揭西"}, {"regionName": "普宁"}], "cityName": "揭阳"}, {"regions": [{"regionName": "电白"}, {"regionName": "高州"}, {"regionName": "化州"}, {"regionName": "茂港"}, {"regionName": "茂南"}, {"regionName": "信宜"}], "cityName": "茂名"}, {"regions": [{"regionName": "大埔"}, {"regionName": "丰顺"}, {"regionName": "蕉岭"}, {"regionName": "梅江"}, {"regionName": "梅县"}, {"regionName": "平远"}, {"regionName": "五华"}, {"regionName": "兴宁"}], "cityName": "梅州"}, {"regions": [{"regionName": "佛冈"}, {"regionName": "连南"}, {"regionName": "连山"}, {"regionName": "连州"}, {"regionName": "清城"}, {"regionName": "清新"}, {"regionName": "英德"}, {"regionName": "阳山"}], "cityName": "清远"}, {"regions": [{"regionName": "宝安"}, {"regionName": "大鹏新区"}, {"regionName": "福田"}, {"regionName": "光明新区"}, {"regionName": "龙岗"}, {"regionName": "罗湖"}, {"regionName": "龙华新区"}, {"regionName": "南山"}, {"regionName": "坪山新区"}, {"regionName": "深圳周边"}, {"regionName": "盐田"}], "cityName": "深圳"}, {"regions": [{"regionName": "浈江"}, {"regionName": "乐昌"}, {"regionName": "南雄"}, {"regionName": "曲江"}, {"regionName": "仁化"}, {"regionName": "乳源"}, {"regionName": "始兴"}, {"regionName": "武江"}, {"regionName": "翁源"}, {"regionName": "新丰"}], "cityName": "韶关"}, {"regions": [{"regionName": "濠江"}, {"regionName": "澄海"}, {"regionName": "潮南"}, {"regionName": "潮阳"}, {"regionName": "金平"}, {"regionName": "龙湖"}, {"regionName": "南澳"}], "cityName": "汕头"}, {"regions": [{"regionName": "城区"}, {"regionName": "海丰"}, {"regionName": "陆丰"}, {"regionName": "陆河"}], "cityName": "汕尾"}, {"regions": [{"regionName": "罗定"}, {"regionName": "新兴"}, {"regionName": "云安"}, {"regionName": "云城"}, {"regionName": "郁南"}], "cityName": "云浮"}, {"regions": [{"regionName": "江城"}, {"regionName": "阳春"}, {"regionName": "阳东"}, {"regionName": "阳西"}], "cityName": "阳江"}, {"regions": [{"regionName": "斗门"}, {"regionName": "金湾"}, {"regionName": "香洲"}, {"regionName": "珠海周边"}], "cityName": "珠海"}, {"regions": [{"regionName": "赤坎"}, {"regionName": "开发区"}, {"regionName": "廉江"}, {"regionName": "雷州"}, {"regionName": "麻章"}, {"regionName": "坡头"}, {"regionName": "遂溪"}, {"regionName": "吴川"}, {"regionName": "霞山"}, {"regionName": "徐闻"}], "cityName": "湛江"}, {"regions": [{"regionName": "鼎湖"}, {"regionName": "德庆"}, {"regionName": "端州"}, {"regionName": "封开"}, {"regionName": "广宁"}, {"regionName": "高要"}, {"regionName": "怀集"}, {"regionName": "四会"}], "cityName": "肇庆"}, {"regions": [{"regionName": "板芙"}, {"regionName": "东凤"}, {"regionName": "东区"}, {"regionName": "东升"}, {"regionName": "大涌"}, {"regionName": "阜沙"}, {"regionName": "港口"}, {"regionName": "古镇"}, {"regionName": "火炬"}, {"regionName": "横栏"}, {"regionName": "黄圃"}, {"regionName": "民众"}, {"regionName": "南朗"}, {"regionName": "南区"}, {"regionName": "南头"}, {"regionName": "石岐"}, {"regionName": "三角"}, {"regionName": "神湾"}, {"regionName": "沙溪"}, {"regionName": "三乡"}, {"regionName": "坦洲"}, {"regionName": "五桂山"}, {"regionName": "小榄"}, {"regionName": "西区"}], "cityName": "中山"}], "provName": "广东"}, {"cities": [{"regions": [{"regionName": "白银区"}, {"regionName": "会宁"}, {"regionName": "景泰"}, {"regionName": "靖远"}, {"regionName": "平川"}], "cityName": "白银"}, {"regions": [{"regionName": "岷县"}, {"regionName": "安定"}, {"regionName": "临洮"}, {"regionName": "陇西"}, {"regionName": "通渭"}, {"regionName": "渭源"}, {"regionName": "漳县"}], "cityName": "定西"}, {"regions": [{"regionName": "迭部"}, {"regionName": "合作"}, {"regionName": "碌曲"}, {"regionName": "临潭"}, {"regionName": "玛曲"}, {"regionName": "夏河"}, {"regionName": "卓尼"}, {"regionName": "舟曲"}], "cityName": "甘南"}, {"regions": [{"regionName": "金川"}, {"regionName": "永昌"}], "cityName": "金昌"}, {"regions": [{"regionName": "阿克塞"}, {"regionName": "敦煌"}, {"regionName": "瓜州"}, {"regionName": "金塔"}, {"regionName": "肃北"}, {"regionName": "肃州"}, {"regionName": "玉门"}], "cityName": "酒泉"}, {"regions": [{"regionName": "长城区"}, {"regionName": "镜铁区"}, {"regionName": "雄关区"}], "cityName": "嘉峪关"}, {"regions": [{"regionName": "宕昌"}, {"regionName": "成县"}, {"regionName": "徽县"}, {"regionName": "康县"}, {"regionName": "两当"}, {"regionName": "礼县"}, {"regionName": "武都"}, {"regionName": "文县"}, {"regionName": "西和"}], "cityName": "陇南"}, {"regions": [{"regionName": "东乡"}, {"regionName": "广河"}, {"regionName": "和政"}, {"regionName": "积石山"}, {"regionName": "康乐"}, {"regionName": "临夏市"}, {"regionName": "永靖"}], "cityName": "临夏"}, {"regions": [{"regionName": "安宁"}, {"regionName": "城关"}, {"regionName": "皋兰"}, {"regionName": "红古"}, {"regionName": "七里河"}, {"regionName": "西固"}, {"regionName": "永登"}, {"regionName": "榆中"}], "cityName": "兰州"}, {"regions": [{"regionName": "崆峒"}, {"regionName": "泾川"}, {"regionName": "崇信"}, {"regionName": "华亭"}, {"regionName": "静宁"}, {"regionName": "灵台"}, {"regionName": "庄浪"}], "cityName": "平凉"}, {"regions": [{"regionName": "华池"}, {"regionName": "合水"}, {"regionName": "环县"}, {"regionName": "宁县"}, {"regionName": "庆城"}, {"regionName": "西峰"}, {"regionName": "正宁"}, {"regionName": "镇原"}], "cityName": "庆阳"}, {"regions": [{"regionName": "北道"}, {"regionName": "甘谷"}, {"regionName": "秦安"}, {"regionName": "秦城"}, {"regionName": "清水"}, {"regionName": "武山"}, {"regionName": "张家川"}], "cityName": "天水"}, {"regions": [{"regionName": "古浪"}, {"regionName": "凉州"}, {"regionName": "民勤"}, {"regionName": "天祝"}], "cityName": "武威"}, {"regions": [{"regionName": "高台"}, {"regionName": "甘州"}, {"regionName": "临泽"}, {"regionName": "民乐"}, {"regionName": "山丹"}, {"regionName": "肃南"}], "cityName": "张掖"}], "provName": "甘肃"}, {"cities": [{"regions": [{"regionName": "海城"}, {"regionName": "合浦"}, {"regionName": "铁山港"}, {"regionName": "银海"}], "cityName": "北海"}, {"regions": [{"regionName": "德保"}, {"regionName": "靖西"}, {"regionName": "隆林"}, {"regionName": "乐业"}, {"regionName": "凌云"}, {"regionName": "那坡"}, {"regionName": "平果"}, {"regionName": "田东"}, {"regionName": "田林"}, {"regionName": "田阳"}, {"regionName": "西林"}, {"regionName": "右江"}], "cityName": "百色"}, {"regions": [{"regionName": "大新"}, {"regionName": "扶绥"}, {"regionName": "江州"}, {"regionName": "龙州"}, {"regionName": "宁明"}, {"regionName": "凭祥"}, {"regionName": "天等"}], "cityName": "崇左"}, {"regions": [{"regionName": "东兴"}, {"regionName": "防城"}, {"regionName": "港口"}, {"regionName": "上思"}], "cityName": "防城港"}, {"regions": [{"regionName": "覃塘"}, {"regionName": "港北"}, {"regionName": "港南"}, {"regionName": "桂平"}, {"regionName": "平南"}], "cityName": "贵港"}, {"regions": [{"regionName": "叠彩"}, {"regionName": "恭城"}, {"regionName": "灌阳"}, {"regionName": "灵川"}, {"regionName": "临桂"}, {"regionName": "荔浦"}, {"regionName": "龙胜"}, {"regionName": "平乐"}, {"regionName": "七星"}, {"regionName": "全州"}, {"regionName": "兴安"}, {"regionName": "秀峰"}, {"regionName": "象山"}, {"regionName": "永福"}, {"regionName": "雁山"}, {"regionName": "阳朔"}, {"regionName": "资源"}], "cityName": "桂林"}, {"regions": [{"regionName": "巴马"}, {"regionName": "都安"}, {"regionName": "大化"}, {"regionName": "东兰"}, {"regionName": "凤山"}, {"regionName": "环江"}, {"regionName": "金城江"}, {"regionName": "罗城"}, {"regionName": "南丹"}, {"regionName": "天峨"}, {"regionName": "宜州"}], "cityName": "河池"}, {"regions": [{"regionName": "八步"}, {"regionName": "富川"}, {"regionName": "昭平"}, {"regionName": "钟山"}], "cityName": "贺州"}, {"regions": [{"regionName": "合山"}, {"regionName": "金秀"}, {"regionName": "武宣"}, {"regionName": "兴宾"}, {"regionName": "忻城"}, {"regionName": "象州"}], "cityName": "来宾"}, {"regions": [{"regionName": "城中"}, {"regionName": "柳北"}, {"regionName": "柳城"}, {"regionName": "柳江"}, {"regionName": "柳南"}, {"regionName": "鹿寨"}, {"regionName": "融安"}, {"regionName": "融水"}, {"regionName": "三江"}, {"regionName": "鱼峰"}], "cityName": "柳州"}, {"regions": [{"regionName": "邕宁"}, {"regionName": "宾阳"}, {"regionName": "横县"}, {"regionName": "江南"}, {"regionName": "隆安"}, {"regionName": "良庆"}, {"regionName": "马山"}, {"regionName": "其他"}, {"regionName": "青秀"}, {"regionName": "上林"}, {"regionName": "武鸣"}, {"regionName": "兴宁"}, {"regionName": "西乡塘"}], "cityName": "南宁"}, {"regions": [{"regionName": "灵山"}, {"regionName": "浦北"}, {"regionName": "钦北"}, {"regionName": "钦南"}], "cityName": "钦州"}, {"regions": [{"regionName": "岑溪"}, {"regionName": "苍梧"}, {"regionName": "长洲"}, {"regionName": "蝶山"}, {"regionName": "蒙山"}, {"regionName": "藤县"}, {"regionName": "万秀"}], "cityName": "梧州"}, {"regions": [{"regionName": "阿尔山"}, {"regionName": "科尔沁右翼前"}, {"regionName": "科尔沁右翼中"}, {"regionName": "突泉"}, {"regionName": "乌兰浩特"}, {"regionName": "扎赉特"}], "cityName": "兴安"}, {"regions": [{"regionName": "博白"}, {"regionName": "北流"}, {"regionName": "陆川"}, {"regionName": "容县"}, {"regionName": "兴业"}, {"regionName": "玉州"}], "cityName": "玉林"}], "provName": "广西"}, {"cities": [{"regions": [{"regionName": "关岭"}, {"regionName": "平坝"}, {"regionName": "普定"}, {"regionName": "西秀"}, {"regionName": "镇宁"}, {"regionName": "紫云"}], "cityName": "安顺"}, {"regions": [{"regionName": "毕节市"}, {"regionName": "大方"}, {"regionName": "赫章"}, {"regionName": "金沙"}, {"regionName": "纳雍"}, {"regionName": "黔西"}, {"regionName": "威宁"}, {"regionName": "织金"}], "cityName": "毕节"}, {"regions": [{"regionName": "白云"}, {"regionName": "花溪"}, {"regionName": "金阳新区"}, {"regionName": "开阳"}, {"regionName": "南明"}, {"regionName": "清镇"}, {"regionName": "乌当"}, {"regionName": "息烽"}, {"regionName": "小河"}, {"regionName": "小河片"}, {"regionName": "修文"}, {"regionName": "云岩"}], "cityName": "贵阳"}, {"regions": [{"regionName": "六枝特区"}, {"regionName": "盘县"}, {"regionName": "水城"}, {"regionName": "钟山"}], "cityName": "六盘水"}, {"regions": [{"regionName": "岑巩"}, {"regionName": "榕江"}, {"regionName": "从江"}, {"regionName": "丹寨"}, {"regionName": "黄平"}, {"regionName": "剑河"}, {"regionName": "锦屏"}, {"regionName": "凯里"}, {"regionName": "黎平"}, {"regionName": "雷山"}, {"regionName": "麻江"}, {"regionName": "施秉"}, {"regionName": "台江"}, {"regionName": "三穗"}, {"regionName": "天柱"}, {"regionName": "镇远"}], "cityName": "黔东南"}, {"regions": [{"regionName": "长顺"}, {"regionName": "独山"}, {"regionName": "都匀"}, {"regionName": "福泉"}, {"regionName": "贵定"}, {"regionName": "惠水"}, {"regionName": "荔波"}, {"regionName": "罗甸"}, {"regionName": "龙里"}, {"regionName": "平塘"}, {"regionName": "三都"}, {"regionName": "瓮安"}], "cityName": "黔南"}, {"regions": [{"regionName": "安龙"}, {"regionName": "册亨"}, {"regionName": "普安"}, {"regionName": "晴隆"}, {"regionName": "望谟"}, {"regionName": "兴仁"}, {"regionName": "兴义"}, {"regionName": "贞丰"}], "cityName": "黔西南"}, {"regions": [{"regionName": "德江"}, {"regionName": "江口"}, {"regionName": "石阡"}, {"regionName": "思南"}, {"regionName": "松桃"}, {"regionName": "铜仁市"}, {"regionName": "万山"}, {"regionName": "沿河"}, {"regionName": "印江"}, {"regionName": "玉屏"}], "cityName": "铜仁"}, {"regions": [{"regionName": "湄潭"}, {"regionName": "赤水"}, {"regionName": "道真"}, {"regionName": "凤冈"}, {"regionName": "汇川"}, {"regionName": "红花岗"}, {"regionName": "仁怀"}, {"regionName": "绥阳"}, {"regionName": "桐梓"}, {"regionName": "务川"}, {"regionName": "习水"}, {"regionName": "余庆"}, {"regionName": "正安"}, {"regionName": "遵义县"}], "cityName": "遵义"}], "provName": "贵州"}, {"cities": [{"regions": [{"regionName": "巴东"}, {"regionName": "恩施市"}, {"regionName": "鹤峰"}, {"regionName": "建始"}, {"regionName": "利川"}, {"regionName": "来凤"}, {"regionName": "宣恩"}, {"regionName": "咸丰"}], "cityName": "恩施"}, {"regions": [{"regionName": "鄂城"}, {"regionName": "华容"}, {"regionName": "梁子湖"}], "cityName": "鄂州"}, {"regions": [{"regionName": "蕲春"}, {"regionName": "浠水"}, {"regionName": "红安"}, {"regionName": "黄梅"}, {"regionName": "黄州"}, {"regionName": "罗田"}, {"regionName": "麻城"}, {"regionName": "团风"}, {"regionName": "武穴"}, {"regionName": "英山"}], "cityName": "黄冈"}, {"regions": [{"regionName": "大冶"}, {"regionName": "黄石港"}, {"regionName": "团城山"}, {"regionName": "铁山"}, {"regionName": "下陆"}, {"regionName": "西塞山"}, {"regionName": "阳新"}], "cityName": "黄石"}, {"regions": [{"regionName": "东宝"}, {"regionName": "掇刀"}, {"regionName": "京山"}, {"regionName": "沙洋"}, {"regionName": "钟祥"}], "cityName": "荆门"}, {"regions": [{"regionName": "公安"}, {"regionName": "洪湖"}, {"regionName": "江陵"}, {"regionName": "监利"}, {"regionName": "荆州区"}, {"regionName": "沙市"}, {"regionName": "石首"}, {"regionName": "松滋"}], "cityName": "荆州"}, {"regions": [{"regionName": "广华"}, {"regionName": "高石碑"}, {"regionName": "浩口"}, {"regionName": "积玉口"}, {"regionName": "龙湾"}, {"regionName": "老新"}, {"regionName": "王场"}, {"regionName": "熊口"}, {"regionName": "园林"}, {"regionName": "杨市"}, {"regionName": "渔洋"}, {"regionName": "周矶"}, {"regionName": "竹根滩"}, {"regionName": "张金"}, {"regionName": "泽口"}], "cityName": "潜江"}, {"regions": [{"regionName": "红坪"}, {"regionName": "九湖"}, {"regionName": "木鱼"}, {"regionName": "松柏"}, {"regionName": "宋洛"}, {"regionName": "下谷平"}, {"regionName": "新华"}, {"regionName": "阳日"}], "cityName": "神农架"}, {"regions": [{"regionName": "丹江口"}, {"regionName": "房县"}, {"regionName": "茅箭"}, {"regionName": "郧西"}, {"regionName": "郧县"}, {"regionName": "竹山"}, {"regionName": "张湾"}, {"regionName": "竹溪"}], "cityName": "十堰"}, {"regions": [{"regionName": "广水"}, {"regionName": "曾都"}], "cityName": "随州"}, {"regions": [{"regionName": "多宝"}, {"regionName": "多祥"}, {"regionName": "佛子山"}, {"regionName": "干驿"}, {"regionName": "候口"}, {"regionName": "横林"}, {"regionName": "黄潭"}, {"regionName": "胡市"}, {"regionName": "蒋场"}, {"regionName": "竟陵"}, {"regionName": "净潭"}, {"regionName": "九真"}, {"regionName": "卢市"}, {"regionName": "马湾"}, {"regionName": "麻洋"}, {"regionName": "彭市"}, {"regionName": "石河"}, {"regionName": "拖市"}, {"regionName": "汪场"}, {"regionName": "小板"}, {"regionName": "岳口"}, {"regionName": "杨林"}, {"regionName": "渔薪"}, {"regionName": "张港"}, {"regionName": "皂市"}], "cityName": "天门"}, {"regions": [{"regionName": "沌口开发区"}, {"regionName": "蔡甸"}, {"regionName": "硚口"}, {"regionName": "东西湖"}, {"regionName": "黄陂"}, {"regionName": "汉南"}, {"regionName": "洪山"}, {"regionName": "汉阳"}, {"regionName": "江岸"}, {"regionName": "江汉"}, {"regionName": "江夏"}, {"regionName": "青山"}, {"regionName": "武昌"}, {"regionName": "新洲"}], "cityName": "武汉"}, {"regions": [{"regionName": "安陆"}, {"regionName": "大悟"}, {"regionName": "汉川"}, {"regionName": "孝昌"}, {"regionName": "孝南"}, {"regionName": "应城"}, {"regionName": "云梦"}], "cityName": "孝感"}, {"regions": [{"regionName": "赤壁"}, {"regionName": "崇阳"}, {"regionName": "嘉鱼"}, {"regionName": "通城"}, {"regionName": "通山"}, {"regionName": "咸安"}], "cityName": "咸宁"}, {"regions": [{"regionName": "沔城"}, {"regionName": "剅河"}, {"regionName": "长埫口"}, {"regionName": "陈场"}, {"regionName": "干河"}, {"regionName": "郭河"}, {"regionName": "工业园"}, {"regionName": "胡场"}, {"regionName": "龙华山"}, {"regionName": "毛嘴"}, {"regionName": "彭场"}, {"regionName": "三伏潭"}, {"regionName": "沙湖"}, {"regionName": "沙嘴"}, {"regionName": "通海口"}, {"regionName": "西流河"}, {"regionName": "杨林尾"}, {"regionName": "郑场"}, {"regionName": "张沟"}], "cityName": "仙桃"}, {"regions": [{"regionName": "保康"}, {"regionName": "樊城"}, {"regionName": "谷城"}, {"regionName": "高新区"}, {"regionName": "老河口"}, {"regionName": "南漳"}, {"regionName": "襄城"}, {"regionName": "襄州"}, {"regionName": "宜城"}, {"regionName": "鱼梁洲"}, {"regionName": "枣阳"}], "cityName": "襄阳"}, {"regions": [{"regionName": "秭归"}, {"regionName": "猇亭"}, {"regionName": "长阳"}, {"regionName": "点军"}, {"regionName": "东山开发区"}, {"regionName": "当阳"}, {"regionName": "五峰"}, {"regionName": "伍家岗"}, {"regionName": "西陵"}, {"regionName": "兴山"}, {"regionName": "远安"}, {"regionName": "宜都"}, {"regionName": "夷陵"}, {"regionName": "枝江"}], "cityName": "宜昌"}], "provName": "湖北"}, {"cities": [{"regions": [{"regionName": "涞水"}, {"regionName": "蠡县"}, {"regionName": "涞源"}, {"regionName": "涿州"}, {"regionName": "安国"}, {"regionName": "安新"}, {"regionName": "保定周边"}, {"regionName": "北市区"}, {"regionName": "博野"}, {"regionName": "定兴"}, {"regionName": "定州"}, {"regionName": "阜平"}, {"regionName": "高碑店"}, {"regionName": "高开区"}, {"regionName": "高阳"}, {"regionName": "满城"}, {"regionName": "南市区"}, {"regionName": "清苑"}, {"regionName": "曲阳"}, {"regionName": "容城"}, {"regionName": "顺平"}, {"regionName": "唐县"}, {"regionName": "望都"}, {"regionName": "徐水"}, {"regionName": "新市区"}, {"regionName": "雄县"}, {"regionName": "易县"}], "cityName": "保定"}, {"regions": [{"regionName": "承德县"}, {"regionName": "丰宁"}, {"regionName": "宽城"}, {"regionName": "隆化"}, {"regionName": "滦平"}, {"regionName": "平泉"}, {"regionName": "双滦区"}, {"regionName": "双桥区"}, {"regionName": "围场"}, {"regionName": "兴隆"}, {"regionName": "鹰手营子"}], "cityName": "承德"}, {"regions": [{"regionName": "泊头"}, {"regionName": "沧县"}, {"regionName": "东光"}, {"regionName": "黄骅"}, {"regionName": "河间"}, {"regionName": "海兴"}, {"regionName": "孟村"}, {"regionName": "南皮"}, {"regionName": "青县"}, {"regionName": "任丘"}, {"regionName": "肃宁"}, {"regionName": "吴桥"}, {"regionName": "新华区"}, {"regionName": "献县"}, {"regionName": "运河区"}, {"regionName": "盐山"}], "cityName": "沧州"}, {"regions": [{"regionName": "成安"}, {"regionName": "丛台区"}, {"regionName": "磁县"}, {"regionName": "大名"}, {"regionName": "峰峰矿区"}, {"regionName": "肥乡"}, {"regionName": "复兴区"}, {"regionName": "高开区"}, {"regionName": "广平"}, {"regionName": "馆陶"}, {"regionName": "邯郸县"}, {"regionName": "邯山区"}, {"regionName": "鸡泽"}, {"regionName": "临漳"}, {"regionName": "邱县"}, {"regionName": "曲周"}, {"regionName": "涉县"}, {"regionName": "武安区"}, {"regionName": "魏县"}, {"regionName": "永年"}], "cityName": "邯郸"}, {"regions": [{"regionName": "安平"}, {"regionName": "阜城"}, {"regionName": "故城"}, {"regionName": "景县"}, {"regionName": "冀州"}, {"regionName": "开发区"}, {"regionName": "饶阳"}, {"regionName": "深州"}, {"regionName": "桃城区"}, {"regionName": "武强"}, {"regionName": "武邑"}, {"regionName": "枣强"}], "cityName": "衡水"}, {"regions": [{"regionName": "安次区"}, {"regionName": "霸州"}, {"regionName": "大厂"}, {"regionName": "大城"}, {"regionName": "固安"}, {"regionName": "广阳区"}, {"regionName": "开发区"}, {"regionName": "三河"}, {"regionName": "文安"}, {"regionName": "香河"}, {"regionName": "燕郊"}, {"regionName": "永清"}], "cityName": "廊坊"}, {"regions": [{"regionName": "北戴河区"}, {"regionName": "昌黎"}, {"regionName": "抚宁"}, {"regionName": "海港区"}, {"regionName": "卢龙"}, {"regionName": "青龙"}, {"regionName": "山海关区"}], "cityName": "秦皇岛"}, {"regions": [{"regionName": "栾城"}, {"regionName": "藁城"}, {"regionName": "长安"}, {"regionName": "高邑"}, {"regionName": "井陉"}, {"regionName": "井陉矿区"}, {"regionName": "晋州"}, {"regionName": "开发区"}, {"regionName": "鹿泉"}, {"regionName": "灵寿"}, {"regionName": "平山"}, {"regionName": "桥东"}, {"regionName": "桥西"}, {"regionName": "深泽"}, {"regionName": "无极"}, {"regionName": "新华"}, {"regionName": "辛集"}, {"regionName": "新乐"}, {"regionName": "行唐"}, {"regionName": "裕华"}, {"regionName": "元氏"}, {"regionName": "正定"}, {"regionName": "赞皇"}, {"regionName": "赵县"}], "cityName": "石家庄"}, {"regions": [{"regionName": "曹妃甸"}, {"regionName": "丰南区"}, {"regionName": "丰润区"}, {"regionName": "高新区"}, {"regionName": "古冶区"}, {"regionName": "海港开发区"}, {"regionName": "汉沽农场"}, {"regionName": "开平区"}, {"regionName": "路北区"}, {"regionName": "滦南"}, {"regionName": "路南区"}, {"regionName": "芦台农场"}, {"regionName": "乐亭"}, {"regionName": "滦县"}, {"regionName": "南堡开发区"}, {"regionName": "迁安"}, {"regionName": "迁西"}, {"regionName": "唐海"}, {"regionName": "玉田"}, {"regionName": "遵化"}], "cityName": "唐山"}, {"regions": [{"regionName": "柏乡"}, {"regionName": "广宗"}, {"regionName": "巨鹿"}, {"regionName": "临城"}, {"regionName": "临西"}, {"regionName": "隆尧"}, {"regionName": "南宫"}, {"regionName": "南和"}, {"regionName": "宁晋"}, {"regionName": "内丘"}, {"regionName": "平乡"}, {"regionName": "桥东区"}, {"regionName": "清河"}, {"regionName": "桥西区"}, {"regionName": "任县"}, {"regionName": "沙河"}, {"regionName": "威县"}, {"regionName": "新河"}, {"regionName": "邢台县"}], "cityName": "邢台"}, {"regions": [{"regionName": "涿鹿"}, {"regionName": "赤城"}, {"regionName": "崇礼"}, {"regionName": "高新区"}, {"regionName": "沽源"}, {"regionName": "怀安"}, {"regionName": "怀来"}, {"regionName": "康保"}, {"regionName": "桥东区"}, {"regionName": "桥西区"}, {"regionName": "尚义"}, {"regionName": "万全"}, {"regionName": "蔚县"}, {"regionName": "宣化"}, {"regionName": "宣化区"}, {"regionName": "下花园区"}, {"regionName": "阳原"}, {"regionName": "张北"}], "cityName": "张家口"}], "provName": "河北"}, {"cities": [{"regions": [{"regionName": "杜尔伯特"}, {"regionName": "大同"}, {"regionName": "红岗"}, {"regionName": "林甸"}, {"regionName": "龙凤"}, {"regionName": "让胡路"}, {"regionName": "萨尔图"}, {"regionName": "肇源"}, {"regionName": "肇州"}], "cityName": "大庆"}, {"regions": [{"regionName": "呼玛"}, {"regionName": "呼中"}, {"regionName": "加格达奇"}, {"regionName": "漠河"}, {"regionName": "塔河"}, {"regionName": "松岭"}, {"regionName": "新林"}], "cityName": "大兴安岭"}, {"regions": [{"regionName": "阿城"}, {"regionName": "宾县"}, {"regionName": "巴彦"}, {"regionName": "道里"}, {"regionName": "道外"}, {"regionName": "方正"}, {"regionName": "江北"}, {"regionName": "开发区"}, {"regionName": "木兰"}, {"regionName": "南岗"}, {"regionName": "平房"}, {"regionName": "双城"}, {"regionName": "尚志"}, {"regionName": "通河"}, {"regionName": "五常"}, {"regionName": "香坊"}, {"regionName": "依兰"}, {"regionName": "延寿"}], "cityName": "哈尔滨"}, {"regions": [{"regionName": "东山"}, {"regionName": "工农"}, {"regionName": "萝北"}, {"regionName": "南山"}, {"regionName": "绥滨"}, {"regionName": "兴安"}, {"regionName": "兴山"}, {"regionName": "向阳"}], "cityName": "鹤岗"}, {"regions": [{"regionName": "爱辉"}, {"regionName": "北安"}, {"regionName": "嫩江"}, {"regionName": "孙吴"}, {"regionName": "五大连池"}, {"regionName": "逊克"}], "cityName": "黑河"}, {"regions": [{"regionName": "桦川"}, {"regionName": "桦南"}, {"regionName": "东风"}, {"regionName": "富锦"}, {"regionName": "抚远"}, {"regionName": "郊区"}, {"regionName": "前进"}, {"regionName": "汤原"}, {"regionName": "同江"}, {"regionName": "向阳"}], "cityName": "佳木斯"}, {"regions": [{"regionName": "城子河"}, {"regionName": "滴道"}, {"regionName": "虎林"}, {"regionName": "恒山"}, {"regionName": "鸡东"}, {"regionName": "鸡冠"}, {"regionName": "梨树"}, {"regionName": "密山"}, {"regionName": "麻山"}], "cityName": "鸡西"}, {"regions": [{"regionName": "爱民"}, {"regionName": "东安"}, {"regionName": "东宁"}, {"regionName": "海林"}, {"regionName": "林口"}, {"regionName": "穆棱"}, {"regionName": "宁安"}, {"regionName": "绥芬河"}, {"regionName": "西安"}, {"regionName": "阳明"}], "cityName": "牡丹江"}, {"regions": [{"regionName": "讷河"}, {"regionName": "昂昂溪"}, {"regionName": "拜泉"}, {"regionName": "富拉尔基"}, {"regionName": "富裕"}, {"regionName": "甘南"}, {"regionName": "建华"}, {"regionName": "克东"}, {"regionName": "克山"}, {"regionName": "龙江"}, {"regionName": "龙沙"}, {"regionName": "梅里斯"}, {"regionName": "碾子山"}, {"regionName": "泰来"}, {"regionName": "铁锋"}, {"regionName": "依安"}], "cityName": "齐齐哈尔"}, {"regions": [{"regionName": "勃利"}, {"regionName": "茄子河"}, {"regionName": "桃山"}, {"regionName": "新兴"}], "cityName": "七台河"}, {"regions": [{"regionName": "安达"}, {"regionName": "北林"}, {"regionName": "海伦"}, {"regionName": "兰西"}, {"regionName": "明水"}, {"regionName": "庆安"}, {"regionName": "青冈"}, {"regionName": "绥棱"}, {"regionName": "望奎"}, {"regionName": "肇东"}], "cityName": "绥化"}, {"regions": [{"regionName": "宝清"}, {"regionName": "宝山"}, {"regionName": "尖山"}, {"regionName": "集贤"}, {"regionName": "岭东"}, {"regionName": "饶河"}, {"regionName": "四方台"}, {"regionName": "友谊"}], "cityName": "双鸭山"}, {"regions": [{"regionName": "翠峦"}, {"regionName": "带岭"}, {"regionName": "红星"}, {"regionName": "金山屯"}, {"regionName": "嘉荫"}, {"regionName": "美溪"}, {"regionName": "南岔"}, {"regionName": "上甘岭"}, {"regionName": "汤旺河"}, {"regionName": "铁力"}, {"regionName": "乌马河"}, {"regionName": "五营"}, {"regionName": "乌伊岭"}, {"regionName": "西林"}, {"regionName": "新青"}, {"regionName": "伊春区"}, {"regionName": "友好"}], "cityName": "伊春"}], "provName": "黑龙江"}, {"cities": [{"regions": [{"regionName": "郾城"}, {"regionName": "临颍"}, {"regionName": "舞阳"}, {"regionName": "源汇"}, {"regionName": "召陵"}], "cityName": "漯河"}, {"regions": [{"regionName": "濮阳县"}, {"regionName": "范县"}, {"regionName": "高新"}, {"regionName": "华龙"}, {"regionName": "南乐"}, {"regionName": "清丰"}, {"regionName": "台前"}], "cityName": "濮阳"}, {"regions": [{"regionName": "安阳县"}, {"regionName": "北关"}, {"regionName": "滑县"}, {"regionName": "龙安"}, {"regionName": "林州"}, {"regionName": "内黄"}, {"regionName": "汤阴"}, {"regionName": "文峰"}, {"regionName": "殷都"}], "cityName": "安阳"}, {"regions": [{"regionName": "淇滨"}, {"regionName": "淇县"}, {"regionName": "鹤山"}, {"regionName": "浚县"}, {"regionName": "山城"}], "cityName": "鹤壁"}, {"regions": [{"regionName": "轵城"}, {"regionName": "北海"}, {"regionName": "承留"}, {"regionName": "大峪"}, {"regionName": "济水"}, {"regionName": "克井"}, {"regionName": "黎林"}, {"regionName": "坡头"}, {"regionName": "沁园"}, {"regionName": "思礼"}, {"regionName": "邵原"}, {"regionName": "天坛"}, {"regionName": "五龙口"}, {"regionName": "王屋"}, {"regionName": "下冶"}, {"regionName": "玉泉"}], "cityName": "济源"}, {"regions": [{"regionName": "博爱"}, {"regionName": "高新"}, {"regionName": "解放"}, {"regionName": "马村"}, {"regionName": "孟州"}, {"regionName": "沁阳"}, {"regionName": "山阳"}, {"regionName": "武陟"}, {"regionName": "温县"}, {"regionName": "修武"}, {"regionName": "中站"}], "cityName": "焦作"}, {"regions": [{"regionName": "杞县"}, {"regionName": "鼓楼"}, {"regionName": "金明"}, {"regionName": "开封县"}, {"regionName": "兰考"}, {"regionName": "龙亭"}, {"regionName": "顺河"}, {"regionName": "通许"}, {"regionName": "尉氏"}, {"regionName": "禹王台"}], "cityName": "开封"}, {"regions": [{"regionName": "栾川"}, {"regionName": "瀍河"}, {"regionName": "偃师"}, {"regionName": "嵩县"}, {"regionName": "吉利"}, {"regionName": "涧西"}, {"regionName": "老城"}, {"regionName": "洛龙"}, {"regionName": "洛宁"}, {"regionName": "孟津"}, {"regionName": "汝阳"}, {"regionName": "新安"}, {"regionName": "西工"}, {"regionName": "伊川"}, {"regionName": "宜阳"}], "cityName": "洛阳"}, {"regions": [{"regionName": "淅川"}, {"regionName": "邓州"}, {"regionName": "方城"}, {"regionName": "内乡"}, {"regionName": "南召"}, {"regionName": "社旗"}, {"regionName": "桐柏"}, {"regionName": "唐河"}, {"regionName": "宛城"}, {"regionName": "卧龙"}, {"regionName": "西峡"}, {"regionName": "新野"}, {"regionName": "油田"}, {"regionName": "镇平"}], "cityName": "南阳"}, {"regions": [{"regionName": "郏县"}, {"regionName": "宝丰"}, {"regionName": "鲁山"}, {"regionName": "汝州"}, {"regionName": "石龙"}, {"regionName": "卫东"}, {"regionName": "舞钢"}, {"regionName": "新华"}, {"regionName": "叶县"}, {"regionName": "湛河"}], "cityName": "平顶山"}, {"regions": [{"regionName": "渑池"}, {"regionName": "湖滨"}, {"regionName": "灵宝"}, {"regionName": "卢氏"}, {"regionName": "陕县"}, {"regionName": "义马"}], "cityName": "三门峡"}, {"regions": [{"regionName": "柘城"}, {"regionName": "睢县"}, {"regionName": "睢阳"}, {"regionName": "梁园"}, {"regionName": "民权"}, {"regionName": "宁陵"}, {"regionName": "夏邑"}, {"regionName": "虞城"}, {"regionName": "永城"}], "cityName": "商丘"}, {"regions": [{"regionName": "鄢陵"}, {"regionName": "长葛"}, {"regionName": "魏都"}, {"regionName": "襄城"}, {"regionName": "许昌县"}, {"regionName": "禹州"}], "cityName": "许昌"}, {"regions": [{"regionName": "长垣"}, {"regionName": "凤泉"}, {"regionName": "封丘"}, {"regionName": "获嘉"}, {"regionName": "红旗"}, {"regionName": "辉县"}, {"regionName": "牧野"}, {"regionName": "卫滨"}, {"regionName": "卫辉"}, {"regionName": "新乡县"}, {"regionName": "延津"}, {"regionName": "原阳"}], "cityName": "新乡"}, {"regions": [{"regionName": "潢川"}, {"regionName": "浉河"}, {"regionName": "固始"}, {"regionName": "光山"}, {"regionName": "淮滨"}, {"regionName": "罗山"}, {"regionName": "平桥"}, {"regionName": "商城"}, {"regionName": "新县"}, {"regionName": "息县"}], "cityName": "信阳"}, {"regions": [{"regionName": "川汇"}, {"regionName": "郸城"}, {"regionName": "扶沟"}, {"regionName": "淮阳"}, {"regionName": "鹿邑"}, {"regionName": "太康"}, {"regionName": "沈丘"}, {"regionName": "商水"}, {"regionName": "项城"}, {"regionName": "西华"}], "cityName": "周口"}, {"regions": [{"regionName": "驿城"}, {"regionName": "泌阳"}, {"regionName": "平舆"}, {"regionName": "确山"}, {"regionName": "汝南"}, {"regionName": "上蔡"}, {"regionName": "遂平"}, {"regionName": "新蔡"}, {"regionName": "西平"}, {"regionName": "正阳"}], "cityName": "驻马店"}, {"regions": [{"regionName": "荥阳"}, {"regionName": "登封"}, {"regionName": "二七"}, {"regionName": "管城"}, {"regionName": "高新区"}, {"regionName": "巩义"}, {"regionName": "惠济"}, {"regionName": "经开区"}, {"regionName": "金水"}, {"regionName": "上街"}, {"regionName": "新密"}, {"regionName": "新郑"}, {"regionName": "郑东"}, {"regionName": "中牟"}, {"regionName": "中原"}], "cityName": "郑州"}], "provName": "河南"}, {"cities": [{"regions": [{"regionName": "澧县"}, {"regionName": "安乡"}, {"regionName": "鼎城"}, {"regionName": "汉寿"}, {"regionName": "津市"}, {"regionName": "临澧"}, {"regionName": "石门"}, {"regionName": "桃源"}, {"regionName": "武陵"}], "cityName": "常德"}, {"regions": [{"regionName": "芙蓉"}, {"regionName": "浏阳"}, {"regionName": "长沙县"}, {"regionName": "经济开发区"}, {"regionName": "开福"}, {"regionName": "宁乡"}, {"regionName": "其他"}, {"regionName": "天心"}, {"regionName": "望城"}, {"regionName": "星沙"}, {"regionName": "雨花"}, {"regionName": "岳麓"}], "cityName": "长沙"}, {"regions": [{"regionName": "安仁"}, {"regionName": "北湖"}, {"regionName": "桂东"}, {"regionName": "桂阳"}, {"regionName": "嘉禾"}, {"regionName": "临武"}, {"regionName": "汝城"}, {"regionName": "苏仙"}, {"regionName": "永兴"}, {"regionName": "宜章"}, {"regionName": "资兴"}], "cityName": "郴州"}, {"regions": [{"regionName": "芷江"}, {"regionName": "沅陵"}, {"regionName": "溆浦"}, {"regionName": "辰溪"}, {"regionName": "鹤城"}, {"regionName": "洪江"}, {"regionName": "会同"}, {"regionName": "靖州"}, {"regionName": "麻阳"}, {"regionName": "通道"}, {"regionName": "新晃"}, {"regionName": "中方"}], "cityName": "怀化"}, {"regions": [{"regionName": "耒阳"}, {"regionName": "常宁"}, {"regionName": "衡东"}, {"regionName": "衡南"}, {"regionName": "衡山"}, {"regionName": "衡阳县"}, {"regionName": "南岳"}, {"regionName": "祁东"}, {"regionName": "石鼓"}, {"regionName": "雁峰"}, {"regionName": "珠晖"}, {"regionName": "蒸湘"}], "cityName": "衡阳"}, {"regions": [{"regionName": "冷水江"}, {"regionName": "娄星"}, {"regionName": "涟源"}, {"regionName": "双峰"}, {"regionName": "新化"}], "cityName": "娄底"}, {"regions": [{"regionName": "北塔"}, {"regionName": "城步"}, {"regionName": "洞口"}, {"regionName": "大祥"}, {"regionName": "隆回"}, {"regionName": "邵东"}, {"regionName": "绥宁"}, {"regionName": "双清"}, {"regionName": "邵阳县"}, {"regionName": "武冈"}, {"regionName": "新宁"}, {"regionName": "新邵"}], "cityName": "邵阳"}, {"regions": [{"regionName": "韶山"}, {"regionName": "湘潭县"}, {"regionName": "湘乡"}, {"regionName": "雨湖"}, {"regionName": "岳塘"}], "cityName": "湘潭"}, {"regions": [{"regionName": "泸溪"}, {"regionName": "保靖"}, {"regionName": "凤凰"}, {"regionName": "古丈"}, {"regionName": "花垣"}, {"regionName": "吉首"}, {"regionName": "龙山"}, {"regionName": "永顺"}], "cityName": "湘西"}, {"regions": [{"regionName": "汨罗"}, {"regionName": "华容"}, {"regionName": "君山"}, {"regionName": "临湘"}, {"regionName": "平江"}, {"regionName": "湘阴"}, {"regionName": "云溪"}, {"regionName": "岳阳楼"}, {"regionName": "岳阳县"}], "cityName": "岳阳"}, {"regions": [{"regionName": "沅江"}, {"regionName": "安化"}, {"regionName": "赫山"}, {"regionName": "南县"}, {"regionName": "桃江"}, {"regionName": "资阳"}], "cityName": "益阳"}, {"regions": [{"regionName": "东安"}, {"regionName": "道县"}, {"regionName": "江华"}, {"regionName": "江永"}, {"regionName": "零陵"}, {"regionName": "蓝山"}, {"regionName": "冷水滩"}, {"regionName": "宁远"}, {"regionName": "祁阳"}, {"regionName": "双牌"}, {"regionName": "新田"}], "cityName": "永州"}, {"regions": [{"regionName": "慈利"}, {"regionName": "桑植"}, {"regionName": "武陵源"}, {"regionName": "永定"}], "cityName": "张家界"}, {"regions": [{"regionName": "醴陵"}, {"regionName": "攸县"}, {"regionName": "茶陵"}, {"regionName": "荷塘"}, {"regionName": "芦淞"}, {"regionName": "石峰"}, {"regionName": "天元"}, {"regionName": "炎陵"}, {"regionName": "株洲县"}], "cityName": "株洲"}], "provName": "湖南"}, {"cities": [{"regions": [{"regionName": "白马井"}, {"regionName": "大成"}, {"regionName": "峨蔓"}, {"regionName": "光村"}, {"regionName": "和庆"}, {"regionName": "海头"}, {"regionName": "兰洋"}, {"regionName": "木棠"}, {"regionName": "那大"}, {"regionName": "南丰"}, {"regionName": "洋浦经济开发区"}, {"regionName": "雅星"}], "cityName": "儋州"}, {"regions": [{"regionName": "龙华"}, {"regionName": "美兰"}, {"regionName": "琼山"}, {"regionName": "其他"}, {"regionName": "秀英"}], "cityName": "海口"}, {"regions": [{"regionName": "博鳌"}, {"regionName": "长坡"}, {"regionName": "大路"}, {"regionName": "会山"}, {"regionName": "嘉积"}, {"regionName": "龙江"}, {"regionName": "石壁"}, {"regionName": "潭门"}, {"regionName": "塔洋"}, {"regionName": "万泉"}, {"regionName": "阳江"}, {"regionName": "中原"}], "cityName": "琼海"}, {"regions": [{"regionName": "大东海"}, {"regionName": "凤凰"}, {"regionName": "凤凰岛"}, {"regionName": "河东"}, {"regionName": "海棠湾"}, {"regionName": "河西"}, {"regionName": "三亚湾"}, {"regionName": "田独"}, {"regionName": "天涯"}, {"regionName": "崖城"}, {"regionName": "育才"}, {"regionName": "亚龙湾"}], "cityName": "三亚"}, {"regions": [{"regionName": "冲山镇"}, {"regionName": "番阳镇"}, {"regionName": "毛阳镇"}, {"regionName": "南圣镇"}, {"regionName": "五指山周边"}], "cityName": "五指山"}], "provName": "海南"}, {"cities": [{"regions": [{"regionName": "洮北区"}, {"regionName": "洮南"}, {"regionName": "大安"}, {"regionName": "通榆"}, {"regionName": "镇赉"}], "cityName": "白城"}, {"regions": [{"regionName": "八道江区"}, {"regionName": "长白"}, {"regionName": "抚松县"}, {"regionName": "江源区"}, {"regionName": "靖宇县"}, {"regionName": "临江市"}], "cityName": "白山"}, {"regions": [{"regionName": "朝阳"}, {"regionName": "德惠"}, {"regionName": "二道"}, {"regionName": "高新"}, {"regionName": "经开"}, {"regionName": "九台"}, {"regionName": "净月"}, {"regionName": "宽城"}, {"regionName": "绿园"}, {"regionName": "农安"}, {"regionName": "南关"}, {"regionName": "汽车城"}, {"regionName": "其他"}, {"regionName": "双阳"}, {"regionName": "榆树"}], "cityName": "长春"}, {"regions": [{"regionName": "桦甸"}, {"regionName": "蛟河"}, {"regionName": "昌邑区"}, {"regionName": "船营区"}, {"regionName": "丰满区"}, {"regionName": "高新区"}, {"regionName": "经开区"}, {"regionName": "龙潭区"}, {"regionName": "磐石"}, {"regionName": "舒兰"}, {"regionName": "永吉"}], "cityName": "吉林"}, {"regions": [{"regionName": "东丰"}, {"regionName": "东辽"}, {"regionName": "龙山区"}, {"regionName": "西安区"}], "cityName": "辽源"}, {"regions": [{"regionName": "公主岭"}, {"regionName": "梨树"}, {"regionName": "双辽"}, {"regionName": "铁东区"}, {"regionName": "铁西区"}, {"regionName": "伊通"}], "cityName": "四平"}, {"regions": [{"regionName": "长岭"}, {"regionName": "扶余"}, {"regionName": "宁江区"}, {"regionName": "乾安"}, {"regionName": "前郭尔罗斯"}], "cityName": "松原"}, {"regions": [{"regionName": "东昌区"}, {"regionName": "二道江区"}, {"regionName": "辉南"}, {"regionName": "集安"}, {"regionName": "柳河"}, {"regionName": "梅河口"}, {"regionName": "通化县"}], "cityName": "通化"}, {"regions": [{"regionName": "珲春"}, {"regionName": "安图"}, {"regionName": "敦化"}, {"regionName": "和龙"}, {"regionName": "龙井"}, {"regionName": "图们"}, {"regionName": "汪清"}, {"regionName": "延吉"}], "cityName": "延边"}], "provName": "吉林"}, {"cities": [{"regions": [{"regionName": "溧阳"}, {"regionName": "金坛"}, {"regionName": "戚墅堰"}, {"regionName": "天宁"}, {"regionName": "武进"}, {"regionName": "新北"}, {"regionName": "钟楼"}], "cityName": "常州"}, {"regions": [{"regionName": "盱眙"}, {"regionName": "楚州"}, {"regionName": "淮阴"}, {"regionName": "洪泽"}, {"regionName": "金湖"}, {"regionName": "经济开发区"}, {"regionName": "涟水"}, {"regionName": "清河"}, {"regionName": "清浦"}], "cityName": "淮安"}, {"regions": [{"regionName": "东海"}, {"regionName": "灌南"}, {"regionName": "赣榆"}, {"regionName": "灌云"}, {"regionName": "海州"}, {"regionName": "连云"}, {"regionName": "新浦"}], "cityName": "连云港"}, {"regions": [{"regionName": "溧水"}, {"regionName": "白下"}, {"regionName": "大厂"}, {"regionName": "高淳"}, {"regionName": "鼓楼"}, {"regionName": "建邺"}, {"regionName": "江宁"}, {"regionName": "六合"}, {"regionName": "南京周边"}, {"regionName": "浦口"}, {"regionName": "秦淮"}, {"regionName": "栖霞"}, {"regionName": "下关"}, {"regionName": "玄武"}, {"regionName": "雨花台"}], "cityName": "南京"}, {"regions": [{"regionName": "崇川"}, {"regionName": "港闸"}, {"regionName": "海安"}, {"regionName": "海门"}, {"regionName": "开发区"}, {"regionName": "启东"}, {"regionName": "如东"}, {"regionName": "如皋"}, {"regionName": "通州"}], "cityName": "南通"}, {"regions": [{"regionName": "泗洪"}, {"regionName": "泗阳"}, {"regionName": "沭阳"}, {"regionName": "宿城区"}, {"regionName": "宿豫"}], "cityName": "宿迁"}, {"regions": [{"regionName": "高港"}, {"regionName": "海陵"}, {"regionName": "靖江"}, {"regionName": "姜堰"}, {"regionName": "泰兴"}, {"regionName": "兴化"}], "cityName": "泰州"}, {"regions": [{"regionName": "沧浪"}, {"regionName": "常熟"}, {"regionName": "金阊"}, {"regionName": "昆山"}, {"regionName": "平江"}, {"regionName": "太仓"}, {"regionName": "吴江"}, {"regionName": "吴中"}, {"regionName": "相城"}, {"regionName": "新区"}, {"regionName": "园区"}, {"regionName": "张家港"}], "cityName": "苏州"}, {"regions": [{"regionName": "滨湖"}, {"regionName": "北塘"}, {"regionName": "崇安"}, {"regionName": "惠山"}, {"regionName": "江阴"}, {"regionName": "南长"}, {"regionName": "新区"}, {"regionName": "锡山"}, {"regionName": "宜兴"}], "cityName": "无锡"}, {"regions": [{"regionName": "睢宁"}, {"regionName": "邳州"}, {"regionName": "丰县"}, {"regionName": "鼓楼"}, {"regionName": "九里"}, {"regionName": "金山桥开发区"}, {"regionName": "贾汪"}, {"regionName": "沛县"}, {"regionName": "泉山"}, {"regionName": "铜山"}, {"regionName": "新城区"}, {"regionName": "新沂"}, {"regionName": "云龙"}], "cityName": "徐州"}, {"regions": [{"regionName": "滨海"}, {"regionName": "大丰"}, {"regionName": "东台"}, {"regionName": "阜宁"}, {"regionName": "建湖"}, {"regionName": "射阳"}, {"regionName": "亭湖"}, {"regionName": "响水"}, {"regionName": "盐都"}], "cityName": "盐城"}, {"regions": [{"regionName": "邗江"}, {"regionName": "宝应"}, {"regionName": "广陵"}, {"regionName": "高邮"}, {"regionName": "江都"}, {"regionName": "开发区"}, {"regionName": "维扬"}, {"regionName": "仪征"}], "cityName": "扬州"}, {"regions": [{"regionName": "丹徒"}, {"regionName": "丹阳"}, {"regionName": "京口"}, {"regionName": "句容"}, {"regionName": "润州"}, {"regionName": "扬中"}, {"regionName": "镇江新区"}], "cityName": "镇江"}], "provName": "江苏"}, {"cities": [{"regions": [{"regionName": "崇仁"}, {"regionName": "东乡"}, {"regionName": "广昌"}, {"regionName": "金溪"}, {"regionName": "乐安"}, {"regionName": "临川"}, {"regionName": "黎川"}, {"regionName": "南城"}, {"regionName": "南丰"}, {"regionName": "宜黄"}, {"regionName": "资溪"}], "cityName": "抚州"}, {"regions": [{"regionName": "安远"}, {"regionName": "崇义"}, {"regionName": "定南"}, {"regionName": "大余"}, {"regionName": "赣县"}, {"regionName": "会昌"}, {"regionName": "龙南"}, {"regionName": "宁都"}, {"regionName": "南康"}, {"regionName": "全南"}, {"regionName": "瑞金"}, {"regionName": "石城"}, {"regionName": "上犹"}, {"regionName": "信丰"}, {"regionName": "兴国"}, {"regionName": "寻乌"}, {"regionName": "于都"}, {"regionName": "章贡"}], "cityName": "赣州"}, {"regions": [{"regionName": "安福"}, {"regionName": "吉安县"}, {"regionName": "井冈山"}, {"regionName": "吉水"}, {"regionName": "吉州"}, {"regionName": "青原"}, {"regionName": "遂川"}, {"regionName": "泰和"}, {"regionName": "万安"}, {"regionName": "新干"}, {"regionName": "峡江"}, {"regionName": "永丰"}, {"regionName": "永新"}], "cityName": "吉安"}, {"regions": [{"regionName": "昌江"}, {"regionName": "浮梁"}, {"regionName": "乐平"}, {"regionName": "珠山"}], "cityName": "景德镇"}, {"regions": [{"regionName": "浔阳"}, {"regionName": "德安"}, {"regionName": "都昌"}, {"regionName": "湖口"}, {"regionName": "九江县"}, {"regionName": "庐山"}, {"regionName": "彭泽"}, {"regionName": "瑞昌"}, {"regionName": "武宁"}, {"regionName": "修水"}, {"regionName": "星子"}, {"regionName": "永修"}], "cityName": "九江"}, {"regions": [{"regionName": "安义"}, {"regionName": "昌北"}, {"regionName": "东湖"}, {"regionName": "高新区"}, {"regionName": "红谷滩新区"}, {"regionName": "进贤"}, {"regionName": "南昌县"}, {"regionName": "青山湖"}, {"regionName": "青云谱"}, {"regionName": "湾里"}, {"regionName": "西湖"}, {"regionName": "新建"}], "cityName": "南昌"}, {"regions": [{"regionName": "安源"}, {"regionName": "莲花"}, {"regionName": "芦溪"}, {"regionName": "上栗"}, {"regionName": "湘东"}], "cityName": "萍乡"}, {"regions": [{"regionName": "鄱阳"}, {"regionName": "婺源"}, {"regionName": "弋阳"}, {"regionName": "德兴"}, {"regionName": "广丰"}, {"regionName": "横峰"}, {"regionName": "铅山"}, {"regionName": "上饶县"}, {"regionName": "万年"}, {"regionName": "信州"}, {"regionName": "余干"}, {"regionName": "玉山"}], "cityName": "上饶"}, {"regions": [{"regionName": "分宜"}, {"regionName": "渝水"}], "cityName": "新余"}, {"regions": [{"regionName": "丰城"}, {"regionName": "奉新"}, {"regionName": "高安"}, {"regionName": "靖安"}, {"regionName": "上高"}, {"regionName": "铜鼓"}, {"regionName": "万载"}, {"regionName": "宜丰"}, {"regionName": "袁州"}, {"regionName": "樟树"}], "cityName": "宜春"}, {"regions": [{"regionName": "贵溪"}, {"regionName": "月湖"}, {"regionName": "余江"}], "cityName": "鹰潭"}], "provName": "江西"}, {"cities": [{"regions": [{"regionName": "岫岩"}, {"regionName": "海城"}, {"regionName": "立山"}, {"regionName": "千山"}, {"regionName": "台安"}, {"regionName": "铁东"}, {"regionName": "铁西"}], "cityName": "鞍山"}, {"regions": [{"regionName": "本溪县"}, {"regionName": "桓仁"}, {"regionName": "明山"}, {"regionName": "南芬"}, {"regionName": "平山"}, {"regionName": "溪湖"}], "cityName": "本溪"}, {"regions": [{"regionName": "北票"}, {"regionName": "朝阳县"}, {"regionName": "建平"}, {"regionName": "喀喇沁左翼"}, {"regionName": "龙城"}, {"regionName": "凌源"}, {"regionName": "双塔"}], "cityName": "朝阳"}, {"regions": [{"regionName": "东港"}, {"regionName": "凤城"}, {"regionName": "宽甸"}, {"regionName": "元宝"}, {"regionName": "振安"}, {"regionName": "振兴"}], "cityName": "丹东"}, {"regions": [{"regionName": "长海"}, {"regionName": "大连周边"}, {"regionName": "甘井子"}, {"regionName": "高新园区"}, {"regionName": "金州"}, {"regionName": "开发区"}, {"regionName": "旅顺口"}, {"regionName": "普兰店"}, {"regionName": "沙河口"}, {"regionName": "瓦房店"}, {"regionName": "西岗"}, {"regionName": "庄河"}, {"regionName": "中山"}], "cityName": "大连"}, {"regions": [{"regionName": "东洲"}, {"regionName": "抚顺县"}, {"regionName": "清原"}, {"regionName": "顺城"}, {"regionName": "望花"}, {"regionName": "新宾"}, {"regionName": "新抚"}], "cityName": "抚顺"}, {"regions": [{"regionName": "阜新县"}, {"regionName": "海州"}, {"regionName": "清河门"}, {"regionName": "太平"}, {"regionName": "细河"}, {"regionName": "新邱"}, {"regionName": "彰武"}], "cityName": "阜新"}, {"regions": [{"regionName": "建昌"}, {"regionName": "龙港"}, {"regionName": "连山"}, {"regionName": "南票"}, {"regionName": "绥中"}, {"regionName": "兴城"}], "cityName": "葫芦岛"}, {"regions": [{"regionName": "北宁"}, {"regionName": "古塔"}, {"regionName": "黑山"}, {"regionName": "凌海"}, {"regionName": "凌河"}, {"regionName": "太和"}, {"regionName": "义县"}], "cityName": "锦州"}, {"regions": [{"regionName": "白塔"}, {"regionName": "灯塔"}, {"regionName": "弓长岭"}, {"regionName": "宏伟"}, {"regionName": "辽阳县"}, {"regionName": "太子河"}, {"regionName": "文圣"}], "cityName": "辽阳"}, {"regions": [{"regionName": "大洼"}, {"regionName": "盘山"}, {"regionName": "双台子"}, {"regionName": "兴隆台"}], "cityName": "盘锦"}, {"regions": [{"regionName": "大东"}, {"regionName": "东陵"}, {"regionName": "法库"}, {"regionName": "皇姑"}, {"regionName": "浑南"}, {"regionName": "和平"}, {"regionName": "康平"}, {"regionName": "辽中"}, {"regionName": "沈北"}, {"regionName": "沈河"}, {"regionName": "苏家屯"}, {"regionName": "铁西"}, {"regionName": "新民"}, {"regionName": "于洪"}], "cityName": "沈阳"}, {"regions": [{"regionName": "昌图"}, {"regionName": "调兵山"}, {"regionName": "开原"}, {"regionName": "清河"}, {"regionName": "铁岭县"}, {"regionName": "西丰"}, {"regionName": "银州"}], "cityName": "铁岭"}, {"regions": [{"regionName": "鲅鱼圈"}, {"regionName": "大石桥"}, {"regionName": "盖州"}, {"regionName": "老边"}, {"regionName": "西市"}, {"regionName": "站前"}], "cityName": "营口"}], "provName": "辽宁"}, {"cities": [{"regions": [{"regionName": "滨河新区"}, {"regionName": "包头周边"}, {"regionName": "白云矿"}, {"regionName": "东河"}, {"regionName": "达茂"}, {"regionName": "固阳"}, {"regionName": "九原"}, {"regionName": "昆都仑"}, {"regionName": "青山"}, {"regionName": "石拐"}, {"regionName": "土默特右"}, {"regionName": "稀土高新区"}], "cityName": "包头"}, {"regions": [{"regionName": "磴口"}, {"regionName": "杭锦后"}, {"regionName": "临河"}, {"regionName": "乌拉特后"}, {"regionName": "乌拉特前"}, {"regionName": "乌拉特中"}, {"regionName": "五原"}], "cityName": "巴彦淖尔"}, {"regions": [{"regionName": "敖汉"}, {"regionName": "阿鲁科尔沁"}, {"regionName": "巴林右"}, {"regionName": "巴林左"}, {"regionName": "红山"}, {"regionName": "喀喇沁"}, {"regionName": "克什克腾"}, {"regionName": "林西"}, {"regionName": "宁城"}, {"regionName": "松山"}, {"regionName": "翁牛特"}, {"regionName": "新城"}, {"regionName": "元宝山"}], "cityName": "赤峰"}, {"regions": [{"regionName": "达拉特"}, {"regionName": "东胜"}, {"regionName": "鄂托克"}, {"regionName": "鄂托克前"}, {"regionName": "杭锦"}, {"regionName": "乌审"}, {"regionName": "伊金霍洛"}, {"regionName": "准格尔"}], "cityName": "鄂尔多斯"}, {"regions": [{"regionName": "和林格尔"}, {"regionName": "回民"}, {"regionName": "金川开发区"}, {"regionName": "金桥开发区"}, {"regionName": "金山开发区"}, {"regionName": "清水河"}, {"regionName": "如意开发区"}, {"regionName": "赛罕"}, {"regionName": "托克托"}, {"regionName": "土默特左"}, {"regionName": "武川"}, {"regionName": "新城"}, {"regionName": "玉泉"}], "cityName": "呼和浩特"}, {"regions": [{"regionName": "阿荣"}, {"regionName": "陈巴尔虎"}, {"regionName": "额尔古纳"}, {"regionName": "鄂伦春自治"}, {"regionName": "鄂温克族自治"}, {"regionName": "根河"}, {"regionName": "海拉尔"}, {"regionName": "莫力达瓦达翰尔族"}, {"regionName": "满洲里"}, {"regionName": "新巴尔虎右"}, {"regionName": "新巴尔虎左"}, {"regionName": "牙克石"}, {"regionName": "扎兰屯"}], "cityName": "呼伦贝尔"}, {"regions": [{"regionName": "霍林郭勒"}, {"regionName": "科尔沁"}, {"regionName": "科尔沁左翼后"}, {"regionName": "科尔沁左翼中"}, {"regionName": "开鲁"}, {"regionName": "库伦"}, {"regionName": "奈曼"}, {"regionName": "扎鲁特"}], "cityName": "通辽"}, {"regions": [{"regionName": "海勃湾"}, {"regionName": "海南"}, {"regionName": "乌达"}], "cityName": "乌海"}, {"regions": [{"regionName": "察哈尔右翼后"}, {"regionName": "察哈尔右翼前"}, {"regionName": "察哈尔右翼中"}, {"regionName": "丰镇"}, {"regionName": "化德"}, {"regionName": "集宁"}, {"regionName": "凉城"}, {"regionName": "商都"}, {"regionName": "四子王"}, {"regionName": "兴和"}, {"regionName": "卓资"}], "cityName": "乌兰察布"}, {"regions": [{"regionName": "阿巴嘎"}, {"regionName": "多伦"}, {"regionName": "东乌珠穆沁"}, {"regionName": "二连浩特"}, {"regionName": "苏尼特右"}, {"regionName": "苏尼特左"}, {"regionName": "太仆寺"}, {"regionName": "镶黄"}, {"regionName": "锡林浩特"}, {"regionName": "西乌珠穆沁"}, {"regionName": "正蓝"}, {"regionName": "正镶白"}], "cityName": "锡林郭勒"}], "provName": "内蒙古"}, {"cities": [{"regions": [{"regionName": "泾源"}, {"regionName": "隆德"}, {"regionName": "彭阳"}, {"regionName": "西吉"}, {"regionName": "原州"}], "cityName": "固原"}, {"regions": [{"regionName": "大武口"}, {"regionName": "惠农"}, {"regionName": "平罗"}], "cityName": "石嘴山"}, {"regions": [{"regionName": "利通"}, {"regionName": "青铜峡"}, {"regionName": "同心"}, {"regionName": "盐池"}], "cityName": "吴忠"}, {"regions": [{"regionName": "贺兰"}, {"regionName": "金凤"}, {"regionName": "灵武"}, {"regionName": "兴庆"}, {"regionName": "西夏"}, {"regionName": "永宁"}], "cityName": "银川"}, {"regions": [{"regionName": "海原"}, {"regionName": "沙坡头"}, {"regionName": "中宁"}], "cityName": "中卫"}], "provName": "宁夏"}, {"cities": [{"regions": [{"regionName": "班玛"}, {"regionName": "达日"}, {"regionName": "甘德"}, {"regionName": "久治"}, {"regionName": "玛多"}, {"regionName": "玛沁"}], "cityName": "果洛"}, {"regions": [{"regionName": "刚察"}, {"regionName": "海晏"}, {"regionName": "门源"}, {"regionName": "祁连"}], "cityName": "海北"}, {"regions": [{"regionName": "化隆"}, {"regionName": "互助"}, {"regionName": "乐都"}, {"regionName": "民和"}, {"regionName": "平安"}, {"regionName": "循化"}], "cityName": "海东"}, {"regions": [{"regionName": "河南"}, {"regionName": "尖扎"}, {"regionName": "同仁"}, {"regionName": "泽库"}], "cityName": "黄南"}, {"regions": [{"regionName": "大柴旦行委"}, {"regionName": "都兰"}, {"regionName": "德令哈"}, {"regionName": "格尔木"}, {"regionName": "冷湖行委"}, {"regionName": "茫崖行委"}, {"regionName": "天峻"}, {"regionName": "乌兰"}], "cityName": "海西"}, {"regions": [{"regionName": "湟源"}, {"regionName": "湟中"}, {"regionName": "城北"}, {"regionName": "城东"}, {"regionName": "城南新区"}, {"regionName": "城西"}, {"regionName": "城中"}, {"regionName": "大通自治县"}, {"regionName": "海湖新区"}, {"regionName": "生物园区"}], "cityName": "西宁"}, {"regions": [{"regionName": "称多"}, {"regionName": "囊谦"}, {"regionName": "曲麻莱"}, {"regionName": "玉树县"}, {"regionName": "治多"}, {"regionName": "杂多"}], "cityName": "玉树"}], "provName": "青海"}, {"cities": [{"regions": [{"regionName": "大堂"}, {"regionName": "风顺堂"}, {"regionName": "花地玛堂"}, {"regionName": "嘉模堂"}, {"regionName": "其他堂区"}, {"regionName": "圣安多尼堂"}, {"regionName": "圣方济各堂"}, {"regionName": "望德堂"}], "cityName": "澳门"}, {"regions": [{"regionName": "荃湾区"}, {"regionName": "北区"}, {"regionName": "大埔区"}, {"regionName": "东区"}, {"regionName": "观塘区"}, {"regionName": "黄大仙区"}, {"regionName": "九龙城区"}, {"regionName": "葵青区"}, {"regionName": "离岛区"}, {"regionName": "南区"}, {"regionName": "深水埗区"}, {"regionName": "沙田区"}, {"regionName": "屯门区"}, {"regionName": "湾仔区"}, {"regionName": "西贡区"}, {"regionName": "油尖旺区"}, {"regionName": "元朗区"}, {"regionName": "中西区"}], "cityName": "香港"}], "provName": "其他"}, {"cities": [{"regions": [{"regionName": "泸县"}, {"regionName": "古蔺"}, {"regionName": "合江"}, {"regionName": "江阳"}, {"regionName": "龙马潭"}, {"regionName": "纳溪"}, {"regionName": "叙永"}], "cityName": "泸州"}, {"regions": [{"regionName": "汶川"}, {"regionName": "阿坝县"}, {"regionName": "黑水"}, {"regionName": "红原"}, {"regionName": "金川"}, {"regionName": "九寨沟"}, {"regionName": "理县"}, {"regionName": "马尔康"}, {"regionName": "茂县"}, {"regionName": "若尔盖"}, {"regionName": "壤塘"}, {"regionName": "松潘"}, {"regionName": "小金"}], "cityName": "阿坝"}, {"regions": [{"regionName": "巴州"}, {"regionName": "南江"}, {"regionName": "平昌"}, {"regionName": "通江"}], "cityName": "巴中"}, {"regions": [{"regionName": "邛崃"}, {"regionName": "郫县"}, {"regionName": "成华"}, {"regionName": "崇州"}, {"regionName": "都江堰"}, {"regionName": "大邑"}, {"regionName": "高新"}, {"regionName": "高新西区"}, {"regionName": "锦江"}, {"regionName": "金牛"}, {"regionName": "金堂"}, {"regionName": "龙泉驿"}, {"regionName": "蒲江"}, {"regionName": "彭州"}, {"regionName": "青白江"}, {"regionName": "其他"}, {"regionName": "青羊"}, {"regionName": "双流"}, {"regionName": "武侯"}, {"regionName": "温江"}, {"regionName": "新都"}, {"regionName": "新津"}], "cityName": "成都"}, {"regions": [{"regionName": "旌阳"}, {"regionName": "广汉"}, {"regionName": "罗江"}, {"regionName": "绵竹"}, {"regionName": "什邡"}, {"regionName": "中江"}], "cityName": "德阳"}, {"regions": [{"regionName": "达县"}, {"regionName": "大竹"}, {"regionName": "开江"}, {"regionName": "渠县"}, {"regionName": "通川"}, {"regionName": "万源"}, {"regionName": "宣汉"}], "cityName": "达州"}, {"regions": [{"regionName": "广安城北"}, {"regionName": "广安城南"}, {"regionName": "广安区"}, {"regionName": "华蓥"}, {"regionName": "邻水"}, {"regionName": "武胜"}, {"regionName": "岳池"}], "cityName": "广安"}, {"regions": [{"regionName": "朝天"}, {"regionName": "苍溪"}, {"regionName": "剑阁"}, {"regionName": "青川"}, {"regionName": "市中"}, {"regionName": "旺苍"}, {"regionName": "元坝"}], "cityName": "广元"}, {"regions": [{"regionName": "泸定"}, {"regionName": "巴塘"}, {"regionName": "白玉"}, {"regionName": "道孚"}, {"regionName": "丹巴"}, {"regionName": "稻城"}, {"regionName": "德格"}, {"regionName": "得荣"}, {"regionName": "甘孜县"}, {"regionName": "九龙"}, {"regionName": "康定"}, {"regionName": "炉霍"}, {"regionName": "理塘"}, {"regionName": "色达"}, {"regionName": "石渠"}, {"regionName": "乡城"}, {"regionName": "新龙"}, {"regionName": "雅江"}], "cityName": "甘孜"}, {"regions": [{"regionName": "沐川"}, {"regionName": "犍为"}, {"regionName": "峨边"}, {"regionName": "峨眉山"}, {"regionName": "夹江"}, {"regionName": "金口河"}, {"regionName": "井研"}, {"regionName": "马边"}, {"regionName": "沙湾"}, {"regionName": "市中"}, {"regionName": "五通桥"}], "cityName": "乐山"}, {"regions": [{"regionName": "布拖"}, {"regionName": "德昌"}, {"regionName": "甘洛"}, {"regionName": "会东"}, {"regionName": "会理"}, {"regionName": "金阳"}, {"regionName": "雷波"}, {"regionName": "美姑"}, {"regionName": "木里"}, {"regionName": "冕宁"}, {"regionName": "宁南"}, {"regionName": "普格"}, {"regionName": "西昌"}, {"regionName": "喜德"}, {"regionName": "越西"}, {"regionName": "盐源"}, {"regionName": "昭觉"}], "cityName": "凉山"}, {"regions": [{"regionName": "丹棱"}, {"regionName": "东坡"}, {"regionName": "洪雅"}, {"regionName": "彭山"}, {"regionName": "青神"}, {"regionName": "仁寿"}], "cityName": "眉山"}, {"regions": [{"regionName": "梓潼"}, {"regionName": "安县"}, {"regionName": "北川"}, {"regionName": "涪城"}, {"regionName": "高新"}, {"regionName": "经开"}, {"regionName": "江油"}, {"regionName": "科创园"}, {"regionName": "平武"}, {"regionName": "三台"}, {"regionName": "盐亭"}, {"regionName": "游仙"}], "cityName": "绵阳"}, {"regions": [{"regionName": "阆中"}, {"regionName": "高坪"}, {"regionName": "嘉陵"}, {"regionName": "南部"}, {"regionName": "蓬安"}, {"regionName": "顺庆"}, {"regionName": "西充"}, {"regionName": "仪陇"}, {"regionName": "营山"}], "cityName": "南充"}, {"regions": [{"regionName": "东兴"}, {"regionName": "隆昌"}, {"regionName": "市中"}, {"regionName": "威远"}, {"regionName": "资中"}], "cityName": "内江"}, {"regions": [{"regionName": "东区"}, {"regionName": "米易"}, {"regionName": "仁和"}, {"regionName": "西区"}, {"regionName": "盐边"}], "cityName": "攀枝花"}, {"regions": [{"regionName": "安居"}, {"regionName": "船山"}, {"regionName": "大英"}, {"regionName": "蓬溪"}, {"regionName": "射洪"}], "cityName": "遂宁"}, {"regions": [{"regionName": "荥经"}, {"regionName": "宝兴"}, {"regionName": "汉源"}, {"regionName": "芦山"}, {"regionName": "名山"}, {"regionName": "石棉"}, {"regionName": "天全"}, {"regionName": "雨城"}], "cityName": "雅安"}, {"regions": [{"regionName": "筠连"}, {"regionName": "珙县"}, {"regionName": "长宁"}, {"regionName": "翠屏"}, {"regionName": "高县"}, {"regionName": "江安"}, {"regionName": "南溪"}, {"regionName": "屏山"}, {"regionName": "兴文"}, {"regionName": "宜宾县"}], "cityName": "宜宾"}, {"regions": [{"regionName": "大安"}, {"regionName": "富顺"}, {"regionName": "贡井"}, {"regionName": "荣县"}, {"regionName": "沿滩"}, {"regionName": "自流井"}], "cityName": "自贡"}, {"regions": [{"regionName": "安岳"}, {"regionName": "简阳"}, {"regionName": "乐至"}, {"regionName": "雁江"}], "cityName": "资阳"}], "provName": "四川"}, {"cities": [{"regions": [{"regionName": "滨城"}, {"regionName": "博兴"}, {"regionName": "惠民"}, {"regionName": "无棣"}, {"regionName": "阳信"}, {"regionName": "沾化"}, {"regionName": "邹平"}], "cityName": "滨州"}, {"regions": [{"regionName": "东营区"}, {"regionName": "广饶"}, {"regionName": "河口"}, {"regionName": "垦利"}, {"regionName": "利津"}], "cityName": "东营"}, {"regions": [{"regionName": "德城"}, {"regionName": "乐陵"}, {"regionName": "陵县"}, {"regionName": "临邑"}, {"regionName": "宁津"}, {"regionName": "平原"}, {"regionName": "齐河"}, {"regionName": "庆云"}, {"regionName": "武城"}, {"regionName": "夏津"}, {"regionName": "禹城"}], "cityName": "德州"}, {"regions": [{"regionName": "鄄城"}, {"regionName": "郓城"}, {"regionName": "成武"}, {"regionName": "曹县"}, {"regionName": "东明"}, {"regionName": "定陶"}, {"regionName": "单县"}, {"regionName": "巨野"}, {"regionName": "牡丹"}], "cityName": "菏泽"}, {"regions": [{"regionName": "汶上"}, {"regionName": "泗水"}, {"regionName": "兖州"}, {"regionName": "金乡"}, {"regionName": "嘉祥"}, {"regionName": "梁山"}, {"regionName": "曲阜"}, {"regionName": "任城"}, {"regionName": "市中"}, {"regionName": "微山"}, {"regionName": "鱼台"}, {"regionName": "邹城"}], "cityName": "济宁"}, {"regions": [{"regionName": "长清"}, {"regionName": "高新"}, {"regionName": "槐荫"}, {"regionName": "济阳"}, {"regionName": "历城"}, {"regionName": "历下"}, {"regionName": "平阴"}, {"regionName": "其他"}, {"regionName": "商河"}, {"regionName": "市中"}, {"regionName": "天桥"}, {"regionName": "章丘"}], "cityName": "济南"}, {"regions": [{"regionName": "茌平"}, {"regionName": "莘县"}, {"regionName": "东阿"}, {"regionName": "东昌府"}, {"regionName": "高唐"}, {"regionName": "冠县"}, {"regionName": "临清"}, {"regionName": "阳谷"}], "cityName": "聊城"}, {"regions": [{"regionName": "钢城"}, {"regionName": "莱城"}], "cityName": "莱芜"}, {"regions": [{"regionName": "郯城"}, {"regionName": "莒南"}, {"regionName": "北城新区"}, {"regionName": "苍山"}, {"regionName": "费县"}, {"regionName": "高新区"}, {"regionName": "河东"}, {"regionName": "开发区"}, {"regionName": "临沭"}, {"regionName": "临港"}, {"regionName": "兰山"}, {"regionName": "罗庄"}, {"regionName": "蒙阴"}, {"regionName": "平邑"}, {"regionName": "沂南"}, {"regionName": "沂水"}], "cityName": "临沂"}, {"regions": [{"regionName": "崂山"}, {"regionName": "城阳"}, {"regionName": "黄岛"}, {"regionName": "即墨"}, {"regionName": "胶南"}, {"regionName": "胶州"}, {"regionName": "李沧"}, {"regionName": "莱西"}, {"regionName": "平度"}, {"regionName": "市北"}, {"regionName": "四方"}, {"regionName": "市南"}], "cityName": "青岛"}, {"regions": [{"regionName": "岚山"}, {"regionName": "莒县"}, {"regionName": "东港"}, {"regionName": "高新区"}, {"regionName": "开发区"}, {"regionName": "山海天旅游度假区"}, {"regionName": "石臼"}, {"regionName": "五莲"}, {"regionName": "新市区"}], "cityName": "日照"}, {"regions": [{"regionName": "岱岳"}, {"regionName": "东平"}, {"regionName": "肥城"}, {"regionName": "宁阳"}, {"regionName": "泰山"}, {"regionName": "新泰"}], "cityName": "泰安"}, {"regions": [{"regionName": "安丘"}, {"regionName": "滨海新区"}, {"regionName": "昌乐"}, {"regionName": "昌邑"}, {"regionName": "坊子"}, {"regionName": "高密"}, {"regionName": "高新区"}, {"regionName": "寒亭"}, {"regionName": "经开区"}, {"regionName": "奎文"}, {"regionName": "临朐"}, {"regionName": "青州"}, {"regionName": "寿光"}, {"regionName": "潍城"}, {"regionName": "诸城"}], "cityName": "潍坊"}, {"regions": [{"regionName": "高区"}, {"regionName": "环翠"}, {"regionName": "经区"}, {"regionName": "荣成"}, {"regionName": "乳山"}, {"regionName": "文登"}], "cityName": "威海"}, {"regions": [{"regionName": "长岛"}, {"regionName": "福山"}, {"regionName": "高新"}, {"regionName": "海阳"}, {"regionName": "开发区"}, {"regionName": "龙口"}, {"regionName": "莱山"}, {"regionName": "莱阳"}, {"regionName": "莱州"}, {"regionName": "牟平"}, {"regionName": "蓬莱"}, {"regionName": "栖霞"}, {"regionName": "芝罘"}, {"regionName": "招远"}], "cityName": "烟台"}, {"regions": [{"regionName": "博山"}, {"regionName": "高青"}, {"regionName": "桓台"}, {"regionName": "临淄"}, {"regionName": "沂源"}, {"regionName": "周村"}, {"regionName": "淄川"}, {"regionName": "张店"}], "cityName": "淄博"}, {"regions": [{"regionName": "峄城"}, {"regionName": "滕州"}, {"regionName": "台儿庄"}, {"regionName": "山亭"}, {"regionName": "市中"}, {"regionName": "薛城"}], "cityName": "枣庄"}], "provName": "山东"}, {"cities": [{"regions": [], "cityName": "闵行"}, {"regions": [], "cityName": "宝山"}, {"regions": [], "cityName": "崇明"}, {"regions": [], "cityName": "长宁"}, {"regions": [], "cityName": "奉贤"}, {"regions": [], "cityName": "虹口"}, {"regions": [], "cityName": "黄浦"}, {"regions": [], "cityName": "静安"}, {"regions": [], "cityName": "嘉定"}, {"regions": [], "cityName": "金山"}, {"regions": [], "cityName": "卢湾"}, {"regions": [], "cityName": "南汇"}, {"regions": [], "cityName": "浦东"}, {"regions": [], "cityName": "普陀"}, {"regions": [], "cityName": "青浦"}, {"regions": [], "cityName": "上海周边"}, {"regions": [], "cityName": "松江"}, {"regions": [], "cityName": "徐汇"}, {"regions": [], "cityName": "杨浦"}, {"regions": [], "cityName": "闸北"}], "provName": "上海"}, {"cities": [{"regions": [{"regionName": "岚皋"}, {"regionName": "白河"}, {"regionName": "汉滨"}, {"regionName": "汉阴"}, {"regionName": "宁陕"}, {"regionName": "平利"}, {"regionName": "石泉"}, {"regionName": "旬阳"}, {"regionName": "镇坪"}, {"regionName": "紫阳"}], "cityName": "安康"}, {"regions": [{"regionName": "岐山"}, {"regionName": "麟游"}, {"regionName": "陈仓"}, {"regionName": "扶风"}, {"regionName": "凤县"}, {"regionName": "凤翔"}, {"regionName": "金台"}, {"regionName": "陇县"}, {"regionName": "眉县"}, {"regionName": "千阳"}, {"regionName": "太白"}, {"regionName": "渭滨"}], "cityName": "宝鸡"}, {"regions": [{"regionName": "城固"}, {"regionName": "佛坪"}, {"regionName": "汉台"}, {"regionName": "留坝"}, {"regionName": "略阳"}, {"regionName": "勉县"}, {"regionName": "宁强"}, {"regionName": "南郑"}, {"regionName": "西乡"}, {"regionName": "洋县"}, {"regionName": "镇巴"}], "cityName": "汉中"}, {"regions": [{"regionName": "丹凤"}, {"regionName": "洛南"}, {"regionName": "商南"}, {"regionName": "山阳"}, {"regionName": "商州"}, {"regionName": "镇安"}, {"regionName": "柞水"}], "cityName": "商洛"}, {"regions": [{"regionName": "王益"}, {"regionName": "宜君"}, {"regionName": "印台"}, {"regionName": "耀州"}], "cityName": "铜川"}, {"regions": [{"regionName": "潼关"}, {"regionName": "白水"}, {"regionName": "澄城"}, {"regionName": "大荔"}, {"regionName": "富平"}, {"regionName": "韩城"}, {"regionName": "华县"}, {"regionName": "合阳"}, {"regionName": "华阴"}, {"regionName": "临渭"}, {"regionName": "蒲城"}], "cityName": "渭南"}, {"regions": [{"regionName": "浐灞"}, {"regionName": "灞桥"}, {"regionName": "泾渭新区"}, {"regionName": "沣渭新区"}, {"regionName": "碑林"}, {"regionName": "长安"}, {"regionName": "高陵"}, {"regionName": "高新"}, {"regionName": "户县"}, {"regionName": "临潼"}, {"regionName": "莲湖"}, {"regionName": "蓝田"}, {"regionName": "曲江新区"}, {"regionName": "其他"}, {"regionName": "未央"}, {"regionName": "新城"}, {"regionName": "阎良"}, {"regionName": "雁塔"}, {"regionName": "周至"}], "cityName": "西安"}, {"regions": [{"regionName": "泾阳"}, {"regionName": "彬县"}, {"regionName": "淳化"}, {"regionName": "长武"}, {"regionName": "礼泉"}, {"regionName": "秦都"}, {"regionName": "乾县"}, {"regionName": "三原"}, {"regionName": "渭城"}, {"regionName": "武功"}, {"regionName": "兴平"}, {"regionName": "旬邑"}, {"regionName": "杨陵"}, {"regionName": "永寿"}], "cityName": "咸阳"}, {"regions": [{"regionName": "安塞"}, {"regionName": "宝塔"}, {"regionName": "富县"}, {"regionName": "甘泉"}, {"regionName": "黄龙"}, {"regionName": "黄陵"}, {"regionName": "洛川"}, {"regionName": "吴起"}, {"regionName": "宜川"}, {"regionName": "延川"}, {"regionName": "延长"}, {"regionName": "子长"}, {"regionName": "志丹"}], "cityName": "延安"}, {"regions": [{"regionName": "北郊"}, {"regionName": "定边"}, {"regionName": "东沙"}, {"regionName": "府谷"}, {"regionName": "横山"}, {"regionName": "靖边"}, {"regionName": "佳县"}, {"regionName": "开发区"}, {"regionName": "米脂"}, {"regionName": "南郊"}, {"regionName": "清涧"}, {"regionName": "绥德"}, {"regionName": "神木"}, {"regionName": "市中心"}, {"regionName": "吴堡"}, {"regionName": "西沙"}, {"regionName": "榆阳"}, {"regionName": "子洲"}], "cityName": "榆林"}], "provName": "陕西"}, {"cities": [{"regions": [{"regionName": "城区"}, {"regionName": "长子"}, {"regionName": "长治县"}, {"regionName": "壶关"}, {"regionName": "郊区"}, {"regionName": "黎城"}, {"regionName": "潞城"}, {"regionName": "平顺"}, {"regionName": "沁县"}, {"regionName": "沁源"}, {"regionName": "屯留"}, {"regionName": "武乡"}, {"regionName": "襄垣"}], "cityName": "长治"}, {"regions": [{"regionName": "城区"}, {"regionName": "大同县"}, {"regionName": "广灵"}, {"regionName": "浑源"}, {"regionName": "矿区"}, {"regionName": "灵丘"}, {"regionName": "南郊"}, {"regionName": "天镇"}, {"regionName": "新荣"}, {"regionName": "阳高"}, {"regionName": "左云"}], "cityName": "大同"}, {"regions": [{"regionName": "城区"}, {"regionName": "高平"}, {"regionName": "陵川"}, {"regionName": "沁水"}, {"regionName": "阳城"}, {"regionName": "泽州"}], "cityName": "晋城"}, {"regions": [{"regionName": "和顺"}, {"regionName": "介休"}, {"regionName": "灵石"}, {"regionName": "平遥"}, {"regionName": "祁县"}, {"regionName": "太谷"}, {"regionName": "寿阳"}, {"regionName": "昔阳"}, {"regionName": "榆次"}, {"regionName": "榆社"}, {"regionName": "左权"}], "cityName": "晋中"}, {"regions": [{"regionName": "隰县"}, {"regionName": "安泽"}, {"regionName": "大宁"}, {"regionName": "浮山"}, {"regionName": "汾西"}, {"regionName": "古县"}, {"regionName": "洪洞"}, {"regionName": "侯马"}, {"regionName": "霍州"}, {"regionName": "吉县"}, {"regionName": "蒲县"}, {"regionName": "曲沃"}, {"regionName": "襄汾"}, {"regionName": "乡宁"}, {"regionName": "翼城"}, {"regionName": "尧都"}, {"regionName": "永和"}], "cityName": "临汾"}, {"regions": [{"regionName": "岚县"}, {"regionName": "方山"}, {"regionName": "汾阳"}, {"regionName": "交城"}, {"regionName": "交口"}, {"regionName": "柳林"}, {"regionName": "离石"}, {"regionName": "临县"}, {"regionName": "石楼"}, {"regionName": "文水"}, {"regionName": "兴县"}, {"regionName": "孝义"}, {"regionName": "中阳"}], "cityName": "吕梁"}, {"regions": [{"regionName": "古交"}, {"regionName": "尖草坪"}, {"regionName": "晋源"}, {"regionName": "娄烦"}, {"regionName": "清徐"}, {"regionName": "万柏林"}, {"regionName": "小店"}, {"regionName": "杏花岭"}, {"regionName": "阳曲"}, {"regionName": "迎泽"}], "cityName": "太原"}, {"regions": [{"regionName": "怀仁"}, {"regionName": "平鲁"}, {"regionName": "朔城"}, {"regionName": "山阴"}, {"regionName": "应县"}, {"regionName": "右玉"}], "cityName": "朔州"}, {"regions": [{"regionName": "岢岚"}, {"regionName": "保德"}, {"regionName": "定襄"}, {"regionName": "代县"}, {"regionName": "繁峙"}, {"regionName": "河曲"}, {"regionName": "静乐"}, {"regionName": "宁武"}, {"regionName": "偏关"}, {"regionName": "神池"}, {"regionName": "五台"}, {"regionName": "五寨"}, {"regionName": "忻府"}, {"regionName": "原平"}], "cityName": "忻州"}, {"regions": [{"regionName": "芮城"}, {"regionName": "稷山"}, {"regionName": "绛县"}, {"regionName": "河津"}, {"regionName": "临猗"}, {"regionName": "平陆"}, {"regionName": "万荣"}, {"regionName": "闻喜"}, {"regionName": "新绛"}, {"regionName": "夏县"}, {"regionName": "盐湖"}, {"regionName": "永济"}, {"regionName": "垣曲"}], "cityName": "运城"}, {"regions": [{"regionName": "城区"}, {"regionName": "郊区"}, {"regionName": "矿区"}, {"regionName": "平定"}, {"regionName": "盂县"}], "cityName": "阳泉"}], "provName": "山西"}, {"cities": [{"regions": [], "cityName": "宝坻"}, {"regions": [], "cityName": "北辰"}, {"regions": [], "cityName": "大港"}, {"regions": [], "cityName": "东丽"}, {"regions": [], "cityName": "河北"}, {"regions": [], "cityName": "河东"}, {"regions": [], "cityName": "汉沽"}, {"regions": [], "cityName": "和平"}, {"regions": [], "cityName": "红桥"}, {"regions": [], "cityName": "河西"}, {"regions": [], "cityName": "静海"}, {"regions": [], "cityName": "津南"}, {"regions": [], "cityName": "蓟县"}, {"regions": [], "cityName": "开发区"}, {"regions": [], "cityName": "宁河"}, {"regions": [], "cityName": "南开"}, {"regions": [], "cityName": "塘沽"}, {"regions": [], "cityName": "武清"}, {"regions": [], "cityName": "西青"}], "provName": "天津"}, {"cities": [{"regions": [{"regionName": "措勤"}, {"regionName": "噶尔"}, {"regionName": "革吉"}, {"regionName": "改则"}, {"regionName": "普兰"}, {"regionName": "日土"}, {"regionName": "札达"}], "cityName": "阿里"}, {"regions": [{"regionName": "边坝"}, {"regionName": "八宿"}, {"regionName": "昌都县"}, {"regionName": "察雅"}, {"regionName": "丁青"}, {"regionName": "贡觉"}, {"regionName": "江达"}, {"regionName": "洛隆"}, {"regionName": "类乌齐"}, {"regionName": "芒康"}, {"regionName": "左贡"}], "cityName": "昌都"}, {"regions": [{"regionName": "城关"}, {"regionName": "堆龙德庆"}, {"regionName": "当雄"}, {"regionName": "达孜"}, {"regionName": "林周"}, {"regionName": "墨竹工卡"}, {"regionName": "尼木"}, {"regionName": "曲水"}], "cityName": "拉萨"}, {"regions": [{"regionName": "波密"}, {"regionName": "察隅"}, {"regionName": "工布江达"}, {"regionName": "朗县"}, {"regionName": "林芝县"}, {"regionName": "米林"}, {"regionName": "墨脱"}], "cityName": "林芝"}, {"regions": [{"regionName": "安多"}, {"regionName": "班戈"}, {"regionName": "巴青"}, {"regionName": "比如"}, {"regionName": "嘉黎"}, {"regionName": "尼玛"}, {"regionName": "那曲县"}, {"regionName": "聂荣"}, {"regionName": "双湖"}, {"regionName": "索县"}, {"regionName": "申扎"}], "cityName": "那曲"}, {"regions": [{"regionName": "昂仁"}, {"regionName": "白朗"}, {"regionName": "定结"}, {"regionName": "定日"}, {"regionName": "岗巴"}, {"regionName": "吉隆"}, {"regionName": "江孜"}, {"regionName": "康马"}, {"regionName": "拉孜"}, {"regionName": "聂拉木"}, {"regionName": "南木林"}, {"regionName": "仁布"}, {"regionName": "日喀则市"}, {"regionName": "萨迦"}, {"regionName": "萨嘎"}, {"regionName": "谢通门"}, {"regionName": "亚东"}, {"regionName": "仲巴"}], "cityName": "日喀则"}, {"regions": [{"regionName": "措美"}, {"regionName": "错那"}, {"regionName": "贡嘎"}, {"regionName": "加查"}, {"regionName": "浪卡子"}, {"regionName": "隆子"}, {"regionName": "洛扎"}, {"regionName": "乃东"}, {"regionName": "琼结"}, {"regionName": "曲松"}, {"regionName": "桑日"}, {"regionName": "扎囊"}], "cityName": "山南"}], "provName": "西藏"}, {"cities": [{"regions": [{"regionName": "阿克苏市"}, {"regionName": "阿瓦提"}, {"regionName": "拜城"}, {"regionName": "库车"}, {"regionName": "柯坪"}, {"regionName": "沙雅"}, {"regionName": "乌什"}, {"regionName": "温宿"}, {"regionName": "新和"}], "cityName": "阿克苏"}, {"regions": [{"regionName": "阿拉尔周边"}, {"regionName": "金银川路街道"}, {"regionName": "南口街道"}, {"regionName": "青松路街道"}, {"regionName": "团场"}, {"regionName": "幸福路街道"}], "cityName": "阿拉尔"}, {"regions": [{"regionName": "阿勒泰市"}, {"regionName": "布尔津"}, {"regionName": "福海"}, {"regionName": "富蕴"}, {"regionName": "哈巴河"}, {"regionName": "吉木乃"}, {"regionName": "青河"}], "cityName": "阿勒泰"}, {"regions": [{"regionName": "博乐"}, {"regionName": "精河"}, {"regionName": "温泉"}], "cityName": "博尔塔拉"}, {"regions": [{"regionName": "博湖"}, {"regionName": "和静"}, {"regionName": "和硕"}, {"regionName": "库尔勒"}, {"regionName": "轮台"}, {"regionName": "且末"}, {"regionName": "若羌"}, {"regionName": "尉犁"}, {"regionName": "焉耆"}], "cityName": "巴音郭楞"}, {"regions": [{"regionName": "昌吉市"}, {"regionName": "阜康"}, {"regionName": "呼图壁"}, {"regionName": "吉木萨尔"}, {"regionName": "木垒"}, {"regionName": "玛纳斯"}, {"regionName": "米泉"}, {"regionName": "奇台"}], "cityName": "昌吉"}, {"regions": [{"regionName": "巴里坤"}, {"regionName": "哈密市"}, {"regionName": "伊吾"}], "cityName": "哈密"}, {"regions": [{"regionName": "策勒"}, {"regionName": "和田市"}, {"regionName": "和田县"}, {"regionName": "洛浦"}, {"regionName": "民丰"}, {"regionName": "墨玉"}, {"regionName": "皮山"}, {"regionName": "于田"}], "cityName": "和田"}, {"regions": [{"regionName": "博湖"}, {"regionName": "和静"}, {"regionName": "和硕"}, {"regionName": "库尔勒周边"}, {"regionName": "轮台"}, {"regionName": "且末"}, {"regionName": "若羌"}, {"regionName": "尉犁"}, {"regionName": "焉耆"}], "cityName": "库尔勒"}, {"regions": [{"regionName": "白碱滩"}, {"regionName": "独山子"}, {"regionName": "克拉玛依区"}, {"regionName": "乌尔禾"}], "cityName": "克拉玛依"}, {"regions": [{"regionName": "伽师"}, {"regionName": "巴楚"}, {"regionName": "喀什市"}, {"regionName": "麦盖提"}, {"regionName": "莎车"}, {"regionName": "疏附"}, {"regionName": "疏勒"}, {"regionName": "塔什库尔"}, {"regionName": "叶城"}, {"regionName": "英吉沙"}, {"regionName": "岳普湖"}, {"regionName": "泽普"}], "cityName": "喀什"}, {"regions": [{"regionName": "阿合奇"}, {"regionName": "阿克陶"}, {"regionName": "阿图什"}, {"regionName": "乌恰"}], "cityName": "克孜勒苏"}, {"regions": [{"regionName": "额敏"}, {"regionName": "和布克赛尔"}, {"regionName": "塔城市"}, {"regionName": "沙湾"}, {"regionName": "托里"}, {"regionName": "乌苏"}, {"regionName": "裕民"}], "cityName": "塔城"}, {"regions": [{"regionName": "北泉"}, {"regionName": "东城"}, {"regionName": "红山"}, {"regionName": "老街"}, {"regionName": "石河子乡"}, {"regionName": "新城"}, {"regionName": "向阳"}], "cityName": "石河子"}, {"regions": [{"regionName": "鄯善"}, {"regionName": "托克逊"}, {"regionName": "吐鲁番市"}], "cityName": "吐鲁番"}, {"regions": [{"regionName": "盖米里克"}, {"regionName": "金墩"}, {"regionName": "喀拉拜勒镇"}, {"regionName": "皮恰克松地"}, {"regionName": "其盖麦旦"}, {"regionName": "图木舒克市区"}, {"regionName": "图木舒克周边"}, {"regionName": "图木休克"}, {"regionName": "永安坝"}], "cityName": "图木舒克"}, {"regions": [{"regionName": "101团"}, {"regionName": "102团"}, {"regionName": "103团"}, {"regionName": "军垦路街道"}, {"regionName": "青湖路街道"}, {"regionName": "人民路街道"}, {"regionName": "五家渠周边"}], "cityName": "五家渠"}, {"regions": [{"regionName": "达坂城"}, {"regionName": "东山"}, {"regionName": "开发"}, {"regionName": "米东"}, {"regionName": "水磨沟"}, {"regionName": "沙依巴克"}, {"regionName": "天山"}, {"regionName": "头屯河"}, {"regionName": "乌鲁木齐县"}, {"regionName": "新市"}], "cityName": "乌鲁木齐"}, {"regions": [{"regionName": "察布查尔"}, {"regionName": "巩留"}, {"regionName": "霍城"}, {"regionName": "奎屯"}, {"regionName": "尼勒克"}, {"regionName": "特克斯"}, {"regionName": "新源"}, {"regionName": "伊宁市"}, {"regionName": "伊宁县"}, {"regionName": "昭苏"}], "cityName": "伊犁"}], "provName": "新疆"}, {"cities": [{"regions": [{"regionName": "昌宁"}, {"regionName": "龙陵"}, {"regionName": "隆阳"}, {"regionName": "施甸"}, {"regionName": "腾冲"}], "cityName": "保山"}, {"regions": [{"regionName": "楚雄市"}, {"regionName": "大姚"}, {"regionName": "禄丰"}, {"regionName": "牟定"}, {"regionName": "南华"}, {"regionName": "双柏"}, {"regionName": "武定"}, {"regionName": "姚安"}, {"regionName": "元谋"}, {"regionName": "永仁"}], "cityName": "楚雄"}, {"regions": [{"regionName": "陇川"}, {"regionName": "梁河"}, {"regionName": "潞西"}, {"regionName": "瑞丽"}, {"regionName": "盈江"}], "cityName": "德宏"}, {"regions": [{"regionName": "宾川"}, {"regionName": "大理市"}, {"regionName": "洱源"}, {"regionName": "鹤庆"}, {"regionName": "剑川"}, {"regionName": "弥渡"}, {"regionName": "南涧"}, {"regionName": "巍山"}, {"regionName": "祥云"}, {"regionName": "漾濞"}, {"regionName": "云龙"}, {"regionName": "永平"}], "cityName": "大理"}, {"regions": [{"regionName": "德钦"}, {"regionName": "维西"}, {"regionName": "香格里拉"}], "cityName": "迪庆"}, {"regions": [{"regionName": "泸西"}, {"regionName": "个旧"}, {"regionName": "红河县"}, {"regionName": "河口"}, {"regionName": "金平"}, {"regionName": "建水"}, {"regionName": "开远"}, {"regionName": "绿春"}, {"regionName": "弥勒"}, {"regionName": "蒙自"}, {"regionName": "屏边"}, {"regionName": "石屏"}, {"regionName": "元阳"}], "cityName": "红河"}, {"regions": [{"regionName": "嵩明"}, {"regionName": "安宁"}, {"regionName": "呈贡"}, {"regionName": "东川"}, {"regionName": "富民"}, {"regionName": "官渡"}, {"regionName": "晋宁"}, {"regionName": "禄劝"}, {"regionName": "盘龙"}, {"regionName": "石林"}, {"regionName": "五华"}, {"regionName": "寻甸"}, {"regionName": "西山"}, {"regionName": "宜良"}], "cityName": "昆明"}, {"regions": [{"regionName": "沧源"}, {"regionName": "凤庆"}, {"regionName": "耿马"}, {"regionName": "临翔"}, {"regionName": "双江"}, {"regionName": "永德"}, {"regionName": "云县"}, {"regionName": "镇康"}], "cityName": "临沧"}, {"regions": [{"regionName": "古城"}, {"regionName": "华坪"}, {"regionName": "宁蒗"}, {"regionName": "玉龙"}, {"regionName": "永胜"}], "cityName": "丽江"}, {"regions": [{"regionName": "泸水"}, {"regionName": "福贡"}, {"regionName": "贡山"}, {"regionName": "兰坪"}], "cityName": "怒江"}, {"regions": [{"regionName": "江城"}, {"regionName": "景东"}, {"regionName": "景谷"}, {"regionName": "澜沧"}, {"regionName": "墨江"}, {"regionName": "孟连"}, {"regionName": "宁洱"}, {"regionName": "思茅"}, {"regionName": "西盟"}, {"regionName": "镇沅"}], "cityName": "普洱"}, {"regions": [{"regionName": "麒麟"}, {"regionName": "富源"}, {"regionName": "会泽"}, {"regionName": "陆良"}, {"regionName": "罗平"}, {"regionName": "马龙"}, {"regionName": "师宗"}, {"regionName": "宣威"}, {"regionName": "沾益"}], "cityName": "曲靖"}, {"regions": [{"regionName": "富宁"}, {"regionName": "广南"}, {"regionName": "马关"}, {"regionName": "麻栗坡"}, {"regionName": "丘北"}, {"regionName": "文山市"}, {"regionName": "西畴"}, {"regionName": "砚山"}], "cityName": "文山"}, {"regions": [{"regionName": "勐海"}, {"regionName": "勐腊"}, {"regionName": "景洪"}], "cityName": "西双版纳"}, {"regions": [{"regionName": "澄江"}, {"regionName": "峨山"}, {"regionName": "华宁"}, {"regionName": "红塔"}, {"regionName": "江川"}, {"regionName": "通海"}, {"regionName": "新平"}, {"regionName": "元江"}, {"regionName": "易门"}], "cityName": "玉溪"}, {"regions": [{"regionName": "大关"}, {"regionName": "鲁甸"}, {"regionName": "巧家"}, {"regionName": "水富"}, {"regionName": "绥江"}, {"regionName": "威信"}, {"regionName": "盐津"}, {"regionName": "彝良"}, {"regionName": "永善"}, {"regionName": "镇雄"}, {"regionName": "昭阳"}], "cityName": "昭通"}], "provName": "云南"}, {"cities": [{"regions": [{"regionName": "衢江"}, {"regionName": "常山"}, {"regionName": "江山"}, {"regionName": "柯城"}, {"regionName": "开化"}, {"regionName": "龙游"}], "cityName": "衢州"}, {"regions": [{"regionName": "滨江"}, {"regionName": "淳安"}, {"regionName": "富阳"}, {"regionName": "拱墅"}, {"regionName": "建德"}, {"regionName": "江干"}, {"regionName": "临安"}, {"regionName": "上城"}, {"regionName": "桐庐"}, {"regionName": "下城"}, {"regionName": "西湖"}, {"regionName": "萧山"}, {"regionName": "余杭"}], "cityName": "杭州"}, {"regions": [{"regionName": "安吉"}, {"regionName": "长兴"}, {"regionName": "德清"}, {"regionName": "南浔"}, {"regionName": "吴兴"}], "cityName": "湖州"}, {"regions": [{"regionName": "婺城"}, {"regionName": "东阳"}, {"regionName": "江北"}, {"regionName": "金东"}, {"regionName": "江南"}, {"regionName": "兰溪"}, {"regionName": "磐安"}, {"regionName": "浦江"}, {"regionName": "武义"}, {"regionName": "永康"}, {"regionName": "义乌"}], "cityName": "金华"}, {"regions": [{"regionName": "海宁"}, {"regionName": "海盐"}, {"regionName": "经济开发区"}, {"regionName": "嘉善"}, {"regionName": "南湖"}, {"regionName": "平湖"}, {"regionName": "桐乡"}, {"regionName": "秀洲"}], "cityName": "嘉兴"}, {"regions": [{"regionName": "缙云"}, {"regionName": "景宁"}, {"regionName": "莲都"}, {"regionName": "龙泉"}, {"regionName": "青田"}, {"regionName": "庆元"}, {"regionName": "遂昌"}, {"regionName": "松阳"}, {"regionName": "云和"}], "cityName": "丽水"}, {"regions": [{"regionName": "甬江"}, {"regionName": "鄞州"}, {"regionName": "北仑"}, {"regionName": "慈溪"}, {"regionName": "奉化"}, {"regionName": "海曙"}, {"regionName": "江北"}, {"regionName": "江东"}, {"regionName": "宁海"}, {"regionName": "象山"}, {"regionName": "余姚"}, {"regionName": "镇海"}], "cityName": "宁波"}, {"regions": [{"regionName": "嵊州"}, {"regionName": "绍兴县"}, {"regionName": "上虞"}, {"regionName": "新昌"}, {"regionName": "越城"}, {"regionName": "诸暨"}], "cityName": "绍兴"}, {"regions": [{"regionName": "黄岩"}, {"regionName": "椒江"}, {"regionName": "临海"}, {"regionName": "路桥"}, {"regionName": "三门"}, {"regionName": "天台"}, {"regionName": "温岭"}, {"regionName": "仙居"}, {"regionName": "玉环"}], "cityName": "台州"}, {"regions": [{"regionName": "瓯海"}, {"regionName": "苍南"}, {"regionName": "洞头"}, {"regionName": "鹿城"}, {"regionName": "乐清"}, {"regionName": "龙湾"}, {"regionName": "平阳"}, {"regionName": "瑞安"}, {"regionName": "泰顺"}, {"regionName": "文成"}, {"regionName": "永嘉"}], "cityName": "温州"}, {"regions": [{"regionName": "嵊泗"}, {"regionName": "岱山"}, {"regionName": "定海"}, {"regionName": "普陀"}], "cityName": "舟山"}], "provName": "浙江"}, {"cities": [{"regions": [], "cityName": "綦江"}, {"regions": [], "cityName": "潼南"}, {"regions": [], "cityName": "璧山"}, {"regions": [], "cityName": "北碚"}, {"regions": [], "cityName": "巴南"}, {"regions": [], "cityName": "城口"}, {"regions": [], "cityName": "长寿"}, {"regions": [], "cityName": "大渡口"}, {"regions": [], "cityName": "垫江"}, {"regions": [], "cityName": "大足"}, {"regions": [], "cityName": "丰都"}, {"regions": [], "cityName": "奉节"}, {"regions": [], "cityName": "涪陵"}, {"regions": [], "cityName": "合川"}, {"regions": [], "cityName": "江北"}, {"regions": [], "cityName": "江津"}, {"regions": [], "cityName": "九龙坡"}, {"regions": [], "cityName": "开县"}, {"regions": [], "cityName": "两江新区"}, {"regions": [], "cityName": "梁平"}, {"regions": [], "cityName": "南岸"}, {"regions": [], "cityName": "南川"}, {"regions": [], "cityName": "彭水"}, {"regions": [], "cityName": "黔江"}, {"regions": [], "cityName": "其他市县"}, {"regions": [], "cityName": "荣昌"}, {"regions": [], "cityName": "沙坪坝"}, {"regions": [], "cityName": "双桥"}, {"regions": [], "cityName": "石柱"}, {"regions": [], "cityName": "铜梁"}, {"regions": [], "cityName": "武隆"}, {"regions": [], "cityName": "万盛"}, {"regions": [], "cityName": "巫山"}, {"regions": [], "cityName": "巫溪"}, {"regions": [], "cityName": "万州"}, {"regions": [], "cityName": "秀山"}, {"regions": [], "cityName": "渝北"}, {"regions": [], "cityName": "永川"}, {"regions": [], "cityName": "酉阳"}, {"regions": [], "cityName": "云阳"}, {"regions": [], "cityName": "渝中"}, {"regions": [], "cityName": "忠县"}], "provName": "重庆"}]
function showTips(str){
    alert(str);
    console.log(str);
}

function errLog(str){
    debugger;
    console.log("ERROR:" +str);
    alert(str);
}

function dataProtocolHandler(data,successCallback,failCallback){
    if(data){
        if(data.code===0){
            if(successCallback && typeof successCallback == "function"){
                successCallback(data.data,data.datatype);
            }
        }else{
            if(failCallback && typeof failCallback == "function"){
                failCallback(data.code,data.msg,data.data,data.datatype);
            }else{
                showTips("data msg="+ data.msg+";data.code="+ data.code);
            }
           
        }
    }else{
        showTips("data is null");
    }
}

//header登录态展示处理
//依赖$.cookie

var G_data = G_data || {};
G_data.admin = G_data.admin || {};
if(localStorage){
	G_data.admin = JSON.parse(localStorage.getItem("admin"))|| {};
}



(loginHandler = function () {
	var $navLogin = $("#navLogin"),
		$navRegister = $("#navRegister"),
		$navNickname = $("#navNickname"),
		$navLogout = $("#navLogout"),
		$navVerifyIDNum = $("#navVerifyIDNum"),
		$navOperate = $(".navOperate"),
		$navVerifyDriverLicense = $("#navVerifyDriverLicense");

	if ($.cookie("mark") && $.cookie("username")){
		$navLogin.hide();
		$navRegister.hide();
		$navNickname.show();
		$navLogout.show();
		if(G_data.admin && G_data.admin.username){
			$navNickname.html(G_data.admin.username);
		}
		
	}else{
		$navLogin.show();
		$navRegister.show();
		$navNickname.hide();
		$navLogout.hide();
		$navOperate.hide();

		$navNickname.html("");
	}
	debugger;
	$.each(G_data.admin,function(k,v){
		if(k.indexOf("Permission")>=0){
			if(v){
				$("."+k).show();
			}else{
				$("."+k).hide();
			}
		}
	});

	$("#navNickname").click(function(){
		location.href = "me.html";
	});


	$navLogout.click(function(){
		var loginoutAjax = function(){
			var jqxhr = $.ajax({
				url: "/api/admin/logout",
				type: "POST",
				dataType: "json",
				success: function(data) {
					debugger;
					dataProtocolHandler(data,function(){
						location.href = location.href;
						G_data.admin= {};
						localStorage.setItem("admin","{}");
						
					});
					
				},
				error: function(data) {
					errLog && errLog("loginoutAjax");
				}
			});
		}
		loginoutAjax();
	});
})();



var G_data = G_data || {}

G_data.currentAddInfoMode = "temp"; //默认是临时路线的添加模式
G_data.adminUserId = "53e9cd5915a5e45c43813d1c";
function initAddressSuggest(){
    var myAddress = []
    for(var i =0;i<ADDRESS.length;i++){

        var provName= ADDRESS[i]["provName"];
        if(provName){
            myAddress.push(provName + "-不限-不限");
        }
        if(ADDRESS[i]["cities"]){
            var cities = ADDRESS[i]["cities"];
            for(var j =0;j<cities.length;j++){
                var cityName = cities[j]["cityName"];
                myAddress.push(provName + "-" + cityName + "-不限");
                var regions = cities[j]["regions"];
                for(var k =0;k<regions.length;k++){
                    myAddress.push(provName + "-" + cityName + "-" + regions[k]["regionName"]);
                }
            }
        }
    }
    G_data.myAddress = myAddress;
}
initAddressSuggest(); 

var initTypeahead = function($this){
    var region = new Bloodhound({
                  datumTokenizer: Bloodhound.tokenizers.obj.chinese('value'),
                  queryTokenizer: Bloodhound.tokenizers.chinese,
                  // `states` is an array of state names defined in "The Basics"
                  local: $.map(G_data.myAddress , function(myAddress) { return { value: myAddress }; }),
                  limit:30
                });
     
    // kicks off the loading/processing of `local` and `prefetch`
    region.initialize();
     
     $this.typeahead({
      hint: true,
      highlight: true,
      minLength: 1
    },{
      name: 'region',
      displayKey: 'value',
      // `ttAdapter` wraps the suggestion engine in an adapter that
      // is compatible with the typeahead jQuery plugin
      source: region.ttAdapter()
    });
   
}
initTypeahead($(".typeahead"));


function isPhoneData(str){
    var pattern=/\d{11}|\d{7,8}|\d{3,4}-\d{7,8}/;
    var ret = pattern.exec(str);
    if(ret){
        return ret[0];
    }else{
        return false;
    }
}
$(function() {
    var $goodsRadio = $("#goodsRadio"),
        $trunkRadio= $("#trunkRadio"),
        $nickname = $("#nickname"),
        $phoneNum = $("#phoneNum"),
        $goodsName = $("#goodsName"),
        $goodsWeight = $("#goodsWeight"),
        $goodsPrice = $("#goodsPrice"),
        $trunkType = $(".trunkType"),
        $licensePlate = $("#licensePlate"),
        $trunkLength = $("#trunkLength"),
        $trunkLoad = $("#trunkLoad"),
        $from = $("#from"),
        $to = $("#to"),
        $time = $("#time"),
        $validateTime = $("#validateTime"),
        $comment = $("#comment"),
        $confirmBtn = $(".confirmBtn"),
        $clearBtn = $(".clearBtn"),
        $timeType = $("#timeType");

    
    var numPerPage = 10;
    var modifyingId = null;


    var safeRender =function(key){
        if (key){
            return key;
        }else{
            return "";
        }
    }

var Datepattern=function(d,fmt) {           
    var o = {           
        "M+" : d.getMonth()+1, //月份           
        "d+" : d.getDate(), //日           
        "h+" : d.getHours()%12 == 0 ? 12 : d.getHours()%12, //小时           
        "H+" : d.getHours(), //小时           
        "m+" : d.getMinutes(), //分           
        "s+" : d.getSeconds(), //秒           
        "q+" : Math.floor((d.getMonth()+3)/3), //季度           
        "S" : d.getMilliseconds() //毫秒           
        };           
    var week = {           
    "0" : "/u65e5",           
    "1" : "/u4e00",           
    "2" : "/u4e8c",           
    "3" : "/u4e09",           
    "4" : "/u56db",           
    "5" : "/u4e94",           
    "6" : "/u516d"              
    };           
    if(/(y+)/.test(fmt)){           
        fmt=fmt.replace(RegExp.$1, (d.getFullYear()+"").substr(4 - RegExp.$1.length));           
    }           
    if(/(E+)/.test(fmt)){           
        fmt=fmt.replace(RegExp.$1, ((RegExp.$1.length>1) ? (RegExp.$1.length>2 ? "/u661f/u671f" : "/u5468") : "")+week[d.getDay()+""]);           
    }           
    for(var k in o){           
        if(new RegExp("("+ k +")").test(fmt)){           
            fmt = fmt.replace(RegExp.$1, (RegExp.$1.length==1) ? (o[k]) : (("00"+ o[k]).substr((""+ o[k]).length)));           
        }           
    }           
    return fmt;           
}



    function init(){  
        // var time1 = Datepattern(new Date(),"yyyy-MM-dd HH:mm:ss");   
        // $time.val(time1);
        // $validateTime.val(2);

        showGoodsType();
    }

    function showTrunkType(){
        $(".goods-required").hide();
        $(".trunk-required").show();
        $timeType.html("回程时间:"); 
    }

    function showGoodsType(){
        $(".trunk-required").hide();
        $(".goods-required").show();
        $timeType.html("发货时间:"); 
    }

    function getReqParams(){

        var data = {};

        if($trunkRadio.get(0).checked){
            data.userType = "driver";
            data.billType = "trunk";
        }else if($goodsRadio.get(0).checked){
            data.userType = "owner";
            data.billType = "goods";
        }

        if($nickname.val()==""){
            showTips("称呼不能为空");
            return null;
        }

        if($phoneNum.val()==""){
            showTips("电话号码不能为空");
            return null;
        }else{
            if(!isPhoneData($phoneNum.val())){
                showTips("电话号码格式不对");
                return null
            }
        }


        if($from.val()==""){
            showTips("出发地不能为空");
            return null;
        }else{
            if($from.val().indexOf(" ")>=0){
                showTips("出发地不能有空格");
                return null;
            }

            if($from.val().split("-").length !=3 ){
                showTips("地址必须有两个'-'分割开，如果是广东省，则填 广东省-不限-不限,如果是广东省广州市，则填 广东省-广州市-不限");
                return null;
            }
        }

        if($to.val()==""){
            showTips("目的地不能为空");
            return null;
        }else{
            if($to.val().indexOf(" ")>=0){
                showTips("目的地不能有空格");
                return null;
            }

            if($to.val().split("-").length !=3 ){
                showTips("地址必须有两个'-'分割开，如果是广东省，则填 广东省-不限-不限,如果是广东省广州市，则填 广东省-广州市-不限");
                return null;
            }
        }

        if(+$trunkLength.val() +"" == "NaN"){
            showTips("货车长度必须是数字");
            return null;
        }

        if(+$validateTime.val() +"" == "NaN"){
            showTips("有效期必须是数字");
            return null;
        }

        if(+$goodsWeight.val() +"" == "NaN"){
            showTips("重量必须是数字");
            return null;
        }

        if(+$goodsPrice.val() +"" == "NaN"){
            showTips("货物价格必须是数字");
            return null;
        }

        if(+$trunkLoad.val() +"" == "NaN"){
            showTips("载重必须是数字");
            return null;
        }


        if($time.val()==""){
        }else{
            var getDate = function(str){
                var a = str.split(" ");
                var b1 = a[0].split("-");
                var b2 = a[1].split(":");
                return new Date(b1[0],(b1[1]-1),b1[2],b2[0],b2[1],b2[2])
            }
            try{
                var _d = getDate($time.val());
                data.billTime = (+ _d)/1000;//服务器以秒作为单位；
            }catch(e){
                return null;
                showTips("发布时间的格式不对");
            }
        }

        if($validateTime.val()==""){
        }else{
            var _d = +$validateTime.val();
            if (_d == NaN){
                showTips("有效期的格式不对");
                return null;
            }else{
                data.validTimeSec = _d * 24 * 60 * 60; //服务器以秒作为单位；
            }

        }



        data.fromAddr = $from.val();
        data.toAddr = $to.val();
        data.phoneNum = $phoneNum.val();
        data.comment = $comment.val();
        data.senderName = $nickname.val();
        data.sender = G_data.adminUserId;
        data.userId = G_data.adminUserId;
        data.qqgroup = $("#qqgroup").val();
        data.qqgroupid = $("#qqgroupid").val();
        data.rawText = $("#rawText").val();
        if(data.userType=="owner"){
            if($goodsPrice.val()!=""){
                data.price = $goodsPrice.val();
            }
            if($goodsWeight.val()!=""){
                data.weight = $goodsWeight.val();
            }
            if($goodsName.val()!=""){
                data.material = $goodsName.val();
            }else{
                data.material = "普货";
            }
        
        }else if(data.userType=="driver"){

            $(".trunkType").each(function(k,v){
                if(v.checked){
                    if($(v).val()!="未知车型"){
                        data.trunkType = $(v).val();
                    }
                }
            });
            if($trunkLength.val()!=""){
                data.trunkLength = $trunkLength.val();
            }
            if($trunkLoad.val()!=""){
                data.trunkLoad = $trunkLoad.val();
            }
            if($licensePlate.val()!=""){
                data.licensePlate = $licensePlate.val();
            }
        }else{
            return null;
        }

        return data;
    }


        //  requiredParams = {
    //     "userType":unicode,
    //     "billType": unicode,

    //     "fromAddr": unicode,
    //     "toAddr": unicode,
    //     "billTime": unicode,
    //     "validTimeSec":unicode
    // }

    // optionalParams = {
    //     "comment":unicode,
    //     "IDNumber": unicode,
    //     "price": unicode,
    //     "weight": unicode,
    //     "material": unicode,

    //     "trunkType": unicode,
    //     "trunkLength": unicode,
    //     "trunkLoad": unicode,
    //     "licensePlate": unicode,
    // } 

    function sendBill(){
        var url = "/message/send";
                   
        var param = getReqParams();
        if(param==null){
            return;
        }

        var jqxhr = $.ajax({
            url: url,
            data: param,
            type: "POST",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;
                    $confirmBtn.tooltip({
                        "animation":true,
                        "placement":"top",
                        "title":"发送成功"
                    }).tooltip('show');
                    setTimeout(function(){
                        $confirmBtn.tooltip("hide");
                        $confirmBtn.tooltip("destroy");
                    },1000);

                    // sendBill2();
                });
            },
            error: function(data) {
                errLog && errLog("/api/bill/send error");
            }
        });

        if(modifyingId){
            var urlModify = "/message/modify";

            var jqxhr = $.ajax({
                url: urlModify,
                data: {
                    id : modifyingId
                },
                type: "POST",
                dataType: "json",
                success: function(data) {
                    dataProtocolHandler(data,function(data){
                        debugger;
                        $("#tr_"+modifyingId).hide("fast", function() {
                            $(this).remove();
                        });
                        modifyingId = null;
                    });
                },
                error: function(data) {
                    errLog && errLog("/api/bill/send error");
                    modifyingId = null;
                }
            });
        }
    }


    var secondToHour = function(seconds){
        return seconds/60/24/60 + "天";
    }

    function getToAddMessage(type){
        var url = "/message/get";
        

        var jqxhr = $.ajax({
            url: url,
            data: null,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    renderToAddMessage(data);
                    // location.href = "/";
                });
            },

            error: function(data) {
                errLog && errLog("getToAddMessage");
            }
        });
    }

     // <th>昵称</th>
     //  <th>电话号码</th>
     //  <th>群号</th>
     //  <th>群名称</th>
     //  <th>时间</th>
     //  <th>内容</th>
     //  <th>操作</th>

    var renderToAddMessage = function(data){
        var renderItem = function(data){
            var template = '<tr id="tr_'+ data._id.$oid +'">\
              <td>'+ data.nickname +'</td>\
              <td>'+ data.phonenum +'</td>\
              <td>'+ data.groupname +'</td>\
              <td>'+ data.groupid +'</td>\
              <td>'+ Datepattern(new Date(+data.time),"yyyy-MM-dd HH:mm:ss")    +'</td>\
              <td>'+ data.content  +'</td>\
              <td>\
                <div class="btn-group" data-id= "'+ data._id.$oid+'"">\
                  <button type="button" class="btn btn-danger fail">忽略</button>\
                  <button type="button" class="btn btn-primary done">完成</button>\
                  <button type="button" class="btn btn-success smart_add">添加</button>\
                </div>\
            </td>\
            </tr>';
            return template;
        }

        $("#toAddMessageBody").empty();
        var len = data.length>100? 100: data.length;

        for (var i=0;i<data.length;i++){
            $("#toAddMessageBody").append(renderItem(data[i]));
        };
    }

    


    var renderRefuseData = function(data){
        // renderPage(data,page);

        $("#refuseMessageContainer tbody").empty();

        // <th>编辑者</th>
        // <th>提交时间</th>
        // <th>消息类型</th>
        // <th>称呼</th>
        // <th>电话号码</th>
        // <th>出发地</th>
        // <th>目的地</th>
        // <th>详细信息</th>
        // <th>备注</th>
        // <th>操作</th>

        $.each(data,function(k,v){

            var renderUserType = function(usertype){
                if(usertype=="driver"){
                    return "车源(求货)";
                }else if(usertype=="owner"){
                    return "货源(求车)";
                }else{
                    return "";
                }
            }


            var renderInfo = function(data){
                var ret = "";
                if (data.billType == "trunk"){
                    ret += "车长:" + safeRender(data.trunkLength) + ";";
                    ret += "车辆类型:" + safeRender(data.trunkType) + ";";
                    ret += "回程时间:" + safeRender(data.billTime) + ";";
                }
                if (data.billType == "goods"){
                    ret += "货重:" + safeRender(data.weight) + ";";
                    ret += "货物名称:" + safeRender(data.material) + ";";
                    ret += "发货时间:" + safeRender(data.billTime) + ";";
                }
                ret += "有效期:" + safeRender(data.validTimeSec) + ";";
                return ret;
            }

            var renderItem = function(data){

                var dataStr = JSON.stringify(data);

                var template = '<tr id="tr_'+ data._id.$oid +'">\
                <td>'+ (data.sendTime ?  Datepattern(new Date(data.sendTime * 1000),"yyyy-MM-dd HH:mm:ss") : "") +'</td>\
                <td>'+ renderUserType(data.userType) +'</td>\
                <td>'+ data.senderName +'</td>\
                <td>'+ data.phoneNum +'</td>\
                <td>'+ data.fromAddr +'</td>\
                <td>'+ data.toAddr +'</td>\
                <td>'+ renderInfo(data) +'</td>\
                <td>'+ (data.comment? data.comment:"无") +'</td>\
                <td>'+ (data.reason ? data.reason :"无")  +'</td>\
                <td>'+ (data.rawText? data.rawText:"无") +'</td>\
                <td>\
                    <div class="btn-group" data-data=\'' + dataStr + '\' data-id= "'+ data._id.$oid+'"">\
                      <button type="button" class="btn btn-primary modify">修改</button>\
                       <button type="button" class="btn btn-danger giveup">放弃</button>\
                    </div>\
                </td>\
                </tr>';
                return template;
            } 

            $("#refuseMessageContainer tbody").append(renderItem(v));
        });
    }

    var getRefuseMessage= function(){
        var url = "/message/getRefuse";

        var jqxhr = $.ajax({
            url: url,
            data: null,
            type: "GET",
            dataType: "json",
            success: function(data) {
                dataProtocolHandler(data,function(data){
                    debugger;
                    renderRefuseData(data);
                    // showRegionChart(confirmInfoArray);
                });
            },

            error: function(data) {
                errLog && errLog("getData() error");
            }
        });
    }



    function reset(){
        $nickname.val("");
        $phoneNum.val("");
        $goodsName.val("");
        $goodsWeight.val("");
        $licensePlate.val("");
        $trunkLength.val("");
        $trunkLoad.val("");
        $from.val("");
        $to.val("");
        $comment.val("");

        // var time1 = Datepattern(new Date(),"yyyy-MM-dd HH:mm:ss");   
        $time.val("");
        $validateTime.val("");
        $("#qqgroupid").val("");
        $("#qqgroup").val("");
        $("#rawText").val("");
    }


    function bindEvent(){
        $goodsRadio.click(function(){
            showGoodsType();
            if($nickname.val()=="车源"){
                $nickname.val("货源");
            }
        });

        $trunkRadio.click(function(){
            showTrunkType();
            if($nickname.val()=="货源"){
                $nickname.val("车源");
            }
        });

        $(".route-view-mode").click(function(){
            $(".route-view-mode").removeClass("btn-primary");
            $(".route-view-mode").addClass("btn-default");
            $(this).removeClass("btn-default");
            $(this).addClass("btn-primary");

            G_data.currentAddInfoMode = $(this).data("viewmode");

            $(".form-horizontal").hide();
            $("#"+G_data.currentAddInfoMode + "Form").show();
        });

        $("#updateTime").click(function(){
            var time1 = Datepattern(new Date(),"yyyy-MM-dd HH:mm:ss");   
            $time.val(time1);
        });

        $("#normalGoods").click(function(){
            $goodsName.val("普货");
        });

        $("#normalNickname").click(function(){

            if($trunkRadio.get(0).checked){
                $nickname.val("车源");
            }else if($goodsRadio.get(0).checked){
                $nickname.val("货源");
            }
            
        })

        $clearBtn.click(function(){
            // if(confirm("确定要清空数据吗？")){
                reset();
            // }
        
        });
        $confirmBtn.click(function(){
            // if(confirm("确定要提交吗？")){
                sendBill();
            // }
        });
        

        var small_2_on = true;
        $("#small_2").click(function(){
            if(small_2_on){
                $(this).html("展开");
                small_2_on = false;
                $("#toAddMessageContainer").hide();
            }else{
                $(this).html("收起");
                small_2_on = true;
                $("#toAddMessageContainer").show();
            }
        });


        var hasFullScreen = false;
        $(".fullscreen").click(function(){
            if(!hasFullScreen){
                $(".fullscreen").html("退出全屏");
                $(".my-panel").hide();
                $(".added-list").removeClass("col-sm-8");
                $(".added-list").addClass("col-sm-12");
                hasFullScreen = true;
            }else{
                $(".fullscreen").html("全屏");
                $(".my-panel").show();
                $(".added-list").removeClass("col-sm-12");
                $(".added-list").addClass("col-sm-8");
                hasFullScreen = false;
            }
        });


        var fixed = true;
        $(".my-panel").css({"position":"fixed"});

        $("#my_panel_fixed").click(function(){
            if(!fixed){
                $("#my_panel_fixed").html("滚动");
                $(".my-panel").css({"position":"fixed"});
                // $(".my-panel").css("top","72px");
                fixed = true;
            }else{
                $("#my_panel_fixed").html("固定");
                $(".my-panel").css({"position":"inherit"});
                // $(".my-panel").css("top","0px");
                fixed = false;
            }
        });
        
        $("#getToAddMessage").click(function(){
            getToAddMessage();
        });


        $("#toAddMessageBody").delegate(".fail","click",function(){

            debugger;
            var $this = $(this),
                id = $this.parents().data("id");
            var jqxhr = $.ajax({
                url: "/message/delete",
                data: {
                    "id": id,
                },
                type: "POST",
                dataType: "json",
                success: function(data) {
                    dataProtocolHandler(data,function(data){
                        debugger; 
                        $this.parents().filter("tr").hide("fast", function() {
                            $(this).remove();
                        });
                        // location.href = "/";
                    });
                },

                error: function(data) {
                    errLog && errLog("/message/delete error");
                }
            });
            return false;
        });
        
        $("#toAddMessageBody").delegate(".done","click",function(){

            debugger;
            var $this = $(this),
                id = $this.parents().data("id");

            var jqxhr = $.ajax({
                url: "/message/done",
                data: {
                    "id": id,
                },
                type: "POST",
                dataType: "json",
                success: function(data) {
                    dataProtocolHandler(data,function(data){
                        debugger; 
                        $this.parents().filter("tr").hide("fast", function() {
                            $(this).remove();
                        });
                        // location.href = "/";
                    });
                },

                error: function(data) {
                    errLog && errLog("message/done error");
                }
            });
            return false;
        });

        $("#toAddMessageBody").delegate(".smart_add","click",function(){
            if (G_data.currentAddInfoMode !="temp"){
                return;
            }
            modifyingId = null;
            var $this = $(this),
                id = $this.parents().data("id");

            var $tds = $("#tr_" + id).find("td");
            reset();
            $nickname.val($tds.eq(0).html());
            $phoneNum.val($tds.eq(1).html().split("-").join(""));

            $("#qqgroup").val($tds.eq(2).html());
            $("#qqgroupid").val($tds.eq(3).html());
            $("#rawText").val($tds.eq(5).html());

            // $time.val($tds.eq(2).html());

            var a = $tds.eq(5).html().split("<br>").join("");
            function isImportantData(str){
                var pattern=/\d{11}|\d{7,8}|\d{3,4}-\d{7,8}/;
                var ret = pattern.exec(str);
                if(ret){
                    return ret[0];
                }else{
                    return false;
                }
            }

            function getWeight(str){
                var pattern=/\d+吨|\d+.\d+吨/;
                var ret = pattern.exec(str);
                if(ret){
                    return ret[0];
                }else{
                    return false;
                }
            }

            var weight = getWeight(a);

            if(weight){
                $goodsWeight.val(weight.split("吨").join(""));
            }

            var phone = isImportantData(a);
            if(phone){
                a = a.split(phone).join("").trim();
                a = a.replace(/,+/g,",").replace(/，+/,"，");

                if(a[a.length-1] == "，" || a[a.length-1] == ","){
                    a = a.substring(a,a.length-1);
                }

                a = a.replace(/<.*>/g,""); //去掉Html
                a = a.replace(/货讯：/g,"").replace(/车讯：/g,"");   //去掉货讯车讯
                $comment.val(a);
            }else{
                $comment.val(a);
            }
        });

        $("#refuseMessageContainer").delegate(".modify","click",function(){
            $this = $(this);
            modifyingId = $this.parents().data("id");
            var data = $this.parents().data("data");
            reset();
            debugger;
            $(".tmp_textarea").html(safeRender(data.rawText));

            $nickname.val(safeRender(data.senderName));
            $phoneNum.val(safeRender(data.phoneNum));


            $("#qqgroup").val(safeRender(data.qqgroup));
            $("#qqgroupid").val(safeRender(data.qqgroupid));
            $("#rawText").val(safeRender(data.rawText));
            $comment.val(safeRender(data.comment));
            $from.val(safeRender(data.fromAddr));
            $to.val(safeRender(data.toAddr));

            $goodsName.val(safeRender(data.material));
            $goodsWeight.val(safeRender(data.weight));

            $(".trunkType").each(function(k,v){
                if($(v).val() == data.trunkType){
                    $(v).trigger("click");
                }
            });
            $trunkLength.val(safeRender(data.trunkLength));
            $trunkLoad.val(safeRender(data.trunkLoad));

            $validateTime.val(data.validTimeSec ? data.validTimeSec /(24 * 60 * 60) : "");
            $time.val(data.billTime ? Datepattern(new Date(data.billTime * 1000),"yyyy-MM-dd HH:mm:ss") : "");

            if(data.userType =="owner"){
                $("#goodsRadio").trigger("click");
            }else{
                $("#trunkRadio").trigger("click");
            }

        });


        $("#refuseMessageContainer").delegate(".giveup","click",function(){
            var $this = $(this),
                id = $this.parents().data("id");

            var jqxhr = $.ajax({
                url: "/message/giveup",
                data: {
                    "id": id,
                },
                type: "POST",
                dataType: "json",
                success: function(data) {
                    dataProtocolHandler(data,function(data){
                        debugger; 
                        $this.parents().filter("tr").hide("fast", function() {
                            $(this).remove();
                        });
                    });
                },

                error: function(data) {
                    errLog && errLog("message/giveup error");
                }
            });
            return false;
        });

        window.onscroll = function () { 
            var top = document.documentElement.scrollTop || document.body.scrollTop;
            if(top>0 && fixed){
                $(".my-panel").css("top", "10px");
            }else{
                if(fixed){
                    $(".my-panel").css("top","72px");
                }else{
                    $(".my-panel").css("top","0px");
                }
            }
        }
    }

    bindEvent();
    init();
    getToAddMessage();
    getRefuseMessage();
});
$(function(){
    $("#toAddMessageBody").delegate(".smart_add","click",function(){
        if (G_data.currentAddInfoMode !="regular"){
            return;
        }
        modifyingId = null;
        var $this = $(this),
            id = $this.parents().data("id");

        var $tds = $("#tr_" + id).find("td");
        reset();
        $("#regularNickname").val($tds.eq(0).html());
        $("#regularPhoneNum").val($tds.eq(1).html().split("-").join(""));

        $("#regularQQgroup").val($tds.eq(2).html());
        $("#regularQQgroupid").val($tds.eq(3).html());

        // $time.val($tds.eq(2).html());

        var a = $tds.eq(5).html().split("<br>").join("");
        $("#regularComment").val(a);

    }); 


    function showTrunkType(){
        $(".goods-required").hide();
        $(".trunk-required").show();
    }

    function showGoodsType(){
        $(".trunk-required").hide();
        $(".goods-required").show();
    }

    $("#regularGoodsRadio").click(function(){
        showGoodsType();
        if($("#regularNickname").val()=="车源"){
            $("#regularNickname").val("货源");
        }
    });

    $("#regularTrunkRadio").click(function(){
        showTrunkType();
        if($("#regularNickname").val()=="货源"){
            $("#regularNickname").val("车源");
        }
    });

    $("#regularNormalNickname").click(function(){

            if($("#regularTrunkRadio").get(0).checked){
                $("#regularNickname").val("车源");
            }else if($("#regularGoodsRadio").get(0).checked){
                $("#regularNickname").val("货源");
            }
            
        })

    $(".regularClearBtn").click(function(){
        // if(confirm("确定要清空数据吗？")){
            reset();
        // }
    
    });
    $(".regularConfirmBtn").click(function(){
        // if(confirm("确定要提交吗？")){
            addRegular();
        // }
    });

    $("#regularForm").delegate(".regular-add","click",function(){
        var temp = '<div class="regular-item">\
                  <div class="panel panel-default">\
                    <div class="panel-heading">\
                      <h3 class="panel-title">常规路线\
                        <div class="btn-group">\
                          <button type="button" class="btn btn-success regular-add">新增</button>\
                          <button type="button" class="btn btn-danger regular-delete">删除</button>\
                      </div>\
                      </h3>\
                    </div>\
                  <div class="form-group">\
                    <label for="from" class="col-sm-4 control-label"><span class="required">*</span>出发地:</label>\
                    <div class="col-sm-8 from-route-list">\
                        <input type="text" class="form-control typeahead from-route-value" placeholder="比如：广东-广州-天河">\
                    </div>\
                  </div>\
                  <div class="form-group">\
                    <label for="to" class="col-sm-4 control-label"><span class="required">*</span>目的地:</label>\
                    <div class="col-sm-8 to-route-list">\
                        <input type="text" class="form-control typeahead to-route-value" placeholder="比如：广东-广州-天河">\
                    </div>\
                  </div>\
                  <div class="form-group">\
                    <label class="col-sm-4 control-label">概率:</label>\
                    <div class="col-sm-8">\
                      <input type="text" class="form-control route-probability" placeholder="0 到 1 之间，可不填">\
                    </div>\
                  </div>\
                </div>';
        $("#regularList").append(temp);
        debugger;
        initTypeahead($(".regular-item").last().find(".typeahead"));

        });

    $("#regularForm").delegate(".regular-delete","click",function(){
        debugger;
        if($(".regular-item").size() <=1){
            showTips("至少一条线路");
            return;
        }
        $(this).parents().filter(".regular-item").remove();
    });


    function getReqParams(){

        var data = {};

        if($("#regularTrunkRadio").get(0).checked){
            data.userType = "driver";
        }else{
            data.userType = "owner";
        }

        $(".regularRole").each(function(k,v){
            if(v.checked){
                data.role = $(v).val();
            }
        });


        if($("#regularNickname").val()==""){
            showTips("称呼不能为空");
            return null;
        }

        if($("#regularPhoneNum").val()==""){
            showTips("电话号码不能为空");
            return null;
        }else{
            if(!isPhoneData($("#regularPhoneNum").val())){
                showTips("电话号码格式不对");
                return null
            }
        }

        $(".from-route-value.tt-input").each(function(k,v){
            if($(v).val()==""){
                showTips("出发地不能为空");
                return null;
            }else{
                if($(v).val().indexOf(" ")>=0){
                    showTips("出发地不能有空格");
                    return null;
                }

                if($(v).val().split("-").length !=3 ){
                    showTips("地址必须有两个'-'分割开，如果是广东省，则填 广东省-不限-不限,如果是广东省广州市，则填 广东省-广州市-不限");
                    return null;
                }
            }
        });

        $(".to-route-value.tt-input").each(function(k,v){
            if($(v).val()==""){
                showTips("目的地不能为空");
                return null;
            }else{
                if($(v).val().indexOf(" ")>=0){
                    showTips("目的地不能有空格");
                    return null;
                }

                if($(v).val().split("-").length !=3 ){
                    showTips("地址必须有两个'-'分割开，如果是广东省，则填 广东省-不限-不限,如果是广东省广州市，则填 广东省-广州市-不限");
                    return null;
                }
            }
        });

        if(+$("#regularTrunkLength").val() +"" == "NaN"){
            showTips("货车长度必须是数字");
            return null;
        }

        if(+$("#regularTrunkLoad").val() +"" == "NaN"){
            showTips("载重必须是数字");
            return null;
        }

        var routes = []
        $(".regular-item").each(function(k,v){
            var route = {};
            route.fromAddr = $(v).find(".from-route-value.tt-input").val();
            route.toAddr = $(v).find(".to-route-value.tt-input").val();
            if($(v).find(".route-probability").val()!=""){
                var _d = +$(v).find(".route-probability").val();
                if(_d +"" == "NaN"){
                    showTips("概率必须是0到1之间的数字");
                    return null;
                }
                if(_d<0 || _d >1){
                    showTips("概率必须是0到1之间的数字");
                    return null;
                }

                route.probability = _d;
            }else{
                route.probability = -1;
            }
            routes.push(route);
        });
        data.routes = JSON.stringify(routes);


        data.phoneNum = $("#regularPhoneNum").val();
        data.comment = $("#regularComment").val();
        data.nickName = $("#regularNickname").val();
        data.qqgroup = $("#regularQQgroup").val();
        data.qqgroupid = $("#regularQQgroupid").val();
        
        data.editor = G_data.admin.username || "default";
        data.time = +(new Date());
        if(data.userType=="driver"){

            $(".regularTrunkType").each(function(k,v){
                if(v.checked){
                    if($(v).val()!="未知车型"){
                        data.trunkType = $(v).val();
                    }
                }
            });
            if($("#regularTrunkLength").val()!=""){
                data.trunkLength = $("#regularTrunkLength").val();
            }
            if($("#regularTrunkLoad").val()!=""){
                data.trunkLoad = $("#regularTrunkLoad").val();
            }
        }

        return data;
    }

    function addRegular(){
        var data = getReqParams();
        var url = "http://115.29.8.74:9288/api/regular/add";

            var jqxhr = $.ajax({
                url: url,
                data: data,
                type: "POST",
                dataType: "json",
                success: function(data) {
                    dataProtocolHandler(data,function(data){
                        debugger;
                        $(".regularConfirmBtn").tooltip({
                        "animation":true,
                        "placement":"top",
                        "title":"发送成功"
                        }).tooltip('show');
                        setTimeout(function(){
                            $(".regularConfirmBtn").tooltip("hide");
                            $(".regularConfirmBtn").tooltip("destroy");
                        },1000);
                    });
                },
                error: function(data) {
                    errLog && errLog("http://115.29.8.74:9288/api/regular/get error");
                }
            });
    }


    function reset(){
        debugger;
        $("#regularNickname").val("");
        $("#regularPhoneNum").val(""); 
        $("#regularQQgroup").val("");
        $("#regularQQgroupid").val("");
        $("#regularComment").val("");
        $(".from-route-value.tt-input").val("");
        $(".to-route-value.tt-input").val("");
    }
});