# Ren'Py Live Variable Browser + Editor
# File: variable_browser_editable.rpy
#
# Drop this file into the game's "game/" folder.
# IMPORTANT: remove/rename any older variable_browser.rpy copy so both aren't loaded.
#
# Compatibility target: Ren'Py 8.1.3+ / Ren'Py 8.x.
# Ren'Py 7.x is untested.
#
# Default hotkey: F8 (change _VB_HOTKEY below if needed).
# Click a variable -> edit its value -> Apply.
# Fast mode is default; toggle Deep to include nested list/dict/object values.
#
# WARNING: Editing persistent.* variables writes the new value to persistent data
# on disk, so those changes can affect future game sessions.
#
# Values use Python-style literals:
#   999
#   12.5
#   True
#   False
#   None
#   "text"
#   [1, 2, 3]
#   {"key": 5}

init -999 python:
    import ast
    import types
    import reprlib

    # Change this if F8 conflicts with a game's own key bindings.
    # Examples: "K_F7", "K_F9", "K_F10".
    _VB_HOTKEY = "K_F8"

    _VB_MAX_ROWS = 300
    _VB_MAX_SCAN_ROWS = 3000
    _VB_MAX_DEPTH = 2
    _VB_MAX_REPR = 500
    _vb_last_status = ""
    _vb_rows_cache = {}

    _vb_repr = reprlib.Repr()
    _vb_repr.maxlevel = 2
    _vb_repr.maxdict = 12
    _vb_repr.maxlist = 12
    _vb_repr.maxtuple = 12
    _vb_repr.maxset = 12
    _vb_repr.maxfrozenset = 12
    _vb_repr.maxstring = 240
    _vb_repr.maxother = 240

    def _vb_safe_repr(value, limit=_VB_MAX_REPR):
        # reprlib avoids constructing enormous repr strings for large
        # dictionaries/lists, which makes the browser much faster.
        try:
            text = _vb_repr.repr(value)
        except Exception as e:
            text = "<repr failed: %s>" % (e,)

        text = text.replace("\n", "\\n")

        if len(text) > limit:
            text = text[:limit - 3] + "..."

        return text

    def _vb_clear_cache():
        _vb_rows_cache.clear()

    def _vb_refresh():
        global _vb_last_status
        _vb_clear_cache()
        _vb_last_status = "Variable list refreshed."
        renpy.restart_interaction()

    def _vb_is_noise(name, value):
        if not name or name.startswith("_"):
            return True

        if isinstance(value, (types.ModuleType, type)):
            return True

        if callable(value):
            return True

        return False

    def _vb_can_expand(value):
        if isinstance(value, (dict, list, tuple)):
            return True

        try:
            module_name = type(value).__module__ or ""

            if module_name.startswith(("renpy", "pygame", "builtins")):
                return False

            return hasattr(value, "__dict__")
        except Exception:
            return False

    def _vb_walk(path, value, depth, rows, seen):
        if len(rows) >= _VB_MAX_SCAN_ROWS:
            return

        rows.append((
            path,
            _vb_safe_repr(value),
            type(value).__name__
        ))

        if depth >= _VB_MAX_DEPTH or not _vb_can_expand(value):
            return

        try:
            ident = id(value)

            if ident in seen:
                return

            seen.add(ident)
        except Exception:
            pass

        try:
            if isinstance(value, dict):
                for key, child in list(value.items())[:250]:
                    child_path = "%s[%r]" % (path, key)
                    _vb_walk(child_path, child, depth + 1, rows, seen)

                    if len(rows) >= _VB_MAX_SCAN_ROWS:
                        break

            elif isinstance(value, (list, tuple)):
                for i, child in enumerate(value[:250]):
                    child_path = "%s[%d]" % (path, i)
                    _vb_walk(child_path, child, depth + 1, rows, seen)

                    if len(rows) >= _VB_MAX_SCAN_ROWS:
                        break

            else:
                attrs = vars(value)

                for key in sorted(attrs):
                    if key.startswith("_"):
                        continue

                    try:
                        child = attrs[key]
                    except Exception:
                        continue

                    if callable(child):
                        continue

                    child_path = "%s.%s" % (path, key)
                    _vb_walk(child_path, child, depth + 1, rows, seen)

                    if len(rows) >= _VB_MAX_SCAN_ROWS:
                        break

        except Exception:
            return

    def _vb_build_rows(scope="all", deep=False):
        # Cache the expensive scan. Ren'Py re-evaluates screens frequently,
        # so rebuilding the variable tree on every interaction is very slow.
        cache_key = (scope, bool(deep))
        cached = _vb_rows_cache.get(cache_key)
        if cached is not None:
            return cached

        rows = []
        seen = set()

        def add_root(path, value):
            if deep:
                _vb_walk(path, value, 0, rows, seen)
            else:
                rows.append((path, _vb_safe_repr(value), type(value).__name__))

        if scope in ("all", "store"):
            try:
                items = sorted(vars(renpy.store).items())
            except Exception:
                items = []

            for name, value in items:
                if _vb_is_noise(name, value):
                    continue

                add_root(name, value)

                # Deep mode is intentionally bounded. Shallow mode keeps all
                # roots in the cache so searching does not miss later names.
                if deep and len(rows) >= _VB_MAX_SCAN_ROWS:
                    break

        if scope in ("all", "persistent") and (not deep or len(rows) < _VB_MAX_SCAN_ROWS):
            try:
                pitems = sorted(vars(persistent).items())
            except Exception:
                pitems = []

            for name, value in pitems:
                if not name or name.startswith("_") or callable(value):
                    continue

                add_root("persistent." + name, value)

                if deep and len(rows) >= _VB_MAX_SCAN_ROWS:
                    break

        _vb_rows_cache[cache_key] = rows
        return rows

    def _vb_collect_rows(query="", scope="all", deep=False):
        rows = _vb_build_rows(scope, deep)
        q = (query or "").strip().lower()

        if q:
            rows = [
                row for row in rows
                if q in row[0].lower()
                or q in row[1].lower()
                or q in row[2].lower()
            ]

        # Keep the rendered screen bounded even if shallow mode found many
        # root variables. Searching still operates over the full cached set.
        return rows[:_VB_MAX_ROWS]

    def _vb_get_value(path):
        namespace = vars(renpy.store)
        return eval(path, namespace, namespace)

    def _vb_parse_value(text, current):
        raw = (text or "").strip()

        # Strings are made convenient: plain text stays plain text.
        if isinstance(current, str):
            if len(raw) >= 2 and raw[0] in ("'", '"') and raw[-1] == raw[0]:
                return ast.literal_eval(raw)
            return raw

        # Friendly boolean input.
        if isinstance(current, bool):
            low = raw.lower()

            if low in ("true", "1", "yes", "on"):
                return True

            if low in ("false", "0", "no", "off"):
                return False

            raise ValueError("Boolean must be True or False.")

        # For normal Python-ish values, use literal_eval.
        value = ast.literal_eval(raw)

        # Preserve numeric type where practical.
        if isinstance(current, int) and not isinstance(current, bool):
            return int(value)

        if isinstance(current, float):
            return float(value)

        return value

    def _vb_apply_value(path, text):
        global _vb_last_status

        try:
            if not path:
                raise ValueError("Select a variable first.")

            # Never let the UI overwrite its own helper/internal variables.
            if path.startswith("_vb_") or path.startswith("renpy."):
                raise ValueError("That variable is protected by the browser.")

            namespace = vars(renpy.store)
            current = _vb_get_value(path)
            new_value = _vb_parse_value(text, current)

            namespace["__vb_new_value"] = new_value

            try:
                exec(path + " = __vb_new_value", namespace, namespace)
            finally:
                namespace.pop("__vb_new_value", None)

            # Make persistent changes hit disk as well.
            if path.startswith("persistent."):
                try:
                    renpy.save_persistent()
                except Exception:
                    pass

            _vb_last_status = "Changed %s to %s" % (
                path,
                _vb_safe_repr(_vb_get_value(path), 220)
            )

        except Exception as e:
            _vb_last_status = "ERROR: %s" % (e,)

        _vb_clear_cache()
        renpy.restart_interaction()

    def _vb_toggle():
        if renpy.get_screen("variable_browser"):
            renpy.hide_screen("variable_browser")
        else:
            renpy.show_screen("variable_browser")

        renpy.restart_interaction()

    if "variable_browser_hotkey" not in config.overlay_screens:
        config.overlay_screens.append("variable_browser_hotkey")


screen variable_browser_hotkey():
    zorder 9998
    key _VB_HOTKEY action Function(_vb_toggle)


screen variable_browser():
    modal True
    zorder 9999

    default vb_query = ""
    default vb_scope = "all"
    default vb_deep = False
    default vb_selected = ""
    default vb_selected_value = ""
    default vb_selected_type = ""
    default vb_edit_value = ""
    default vb_search_input = ScreenVariableInputValue("vb_query", default=True)
    default vb_edit_input = ScreenVariableInputValue("vb_edit_value", default=False)

    key _VB_HOTKEY action Hide("variable_browser")
    key "K_ESCAPE" action Hide("variable_browser")

    add Solid("#000000b8")

    frame:
        xalign 0.5
        yalign 0.5
        xsize 1180
        ysize 760
        padding (20, 18)

        vbox:
            spacing 10

            hbox:
                spacing 18

                text "Ren'Py Live Variable Browser + Editor" size 30

                textbutton "All":
                    action SetScreenVariable("vb_scope", "all")

                textbutton "Store":
                    action SetScreenVariable("vb_scope", "store")

                textbutton "Persistent":
                    action SetScreenVariable("vb_scope", "persistent")

                null width 20

                textbutton "Close":
                    action Hide("variable_browser")

            hbox:
                spacing 10

                text "Search:" yalign 0.5

                button:
                    xsize 500
                    ysize 42
                    padding (8, 4)
                    action vb_search_input.Enable()
                    key_events True

                    input:
                        value vb_search_input
                        length 100
                        copypaste True

                text "Scope: [vb_scope]" yalign 0.5

                if vb_deep:
                    textbutton "Deep: On":
                        action SetScreenVariable("vb_deep", False)
                else:
                    textbutton "Deep: Off":
                        action SetScreenVariable("vb_deep", True)

                textbutton "Refresh":
                    action Function(_vb_refresh)

            $ vb_rows = _vb_collect_rows(vb_query, vb_scope, vb_deep)

            if vb_deep:
                text "Deep mode: nested values included. This can be slower." size 18
            else:
                text "Fast mode: top-level variables only. Turn Deep on for nested values." size 18

            if len(vb_rows) >= _VB_MAX_ROWS:
                text "Showing first %d rows — narrow the search." % _VB_MAX_ROWS size 18

            frame:
                xfill True
                ysize 410
                padding (8, 8)

                viewport:
                    mousewheel True
                    draggable True
                    scrollbars "vertical"
                    pagekeys True

                    vbox:
                        spacing 3

                        for vb_path, vb_value, vb_type in vb_rows:
                            button:
                                xfill True

                                action [
                                    SetScreenVariable("vb_selected", vb_path),
                                    SetScreenVariable("vb_selected_value", vb_value),
                                    SetScreenVariable("vb_selected_type", vb_type),
                                    SetScreenVariable("vb_edit_value", vb_value),
                                    vb_edit_input.Enable(),
                                ]

                                hbox:
                                    spacing 12

                                    text "[vb_path!q]" xsize 420 size 18
                                    text "[vb_type!q]" xsize 120 size 16
                                    text "[vb_value!q]" xsize 560 size 16

            frame:
                xfill True
                ysize 175
                padding (10, 8)

                vbox:
                    spacing 7

                    if vb_selected:
                        text "Selected: [vb_selected!q]    ([vb_selected_type!q])" size 20

                        hbox:
                            spacing 10

                            button:
                                xsize 900
                                ysize 42
                                padding (8, 4)
                                action vb_edit_input.Enable()
                                key_events True

                                input:
                                    value vb_edit_input
                                    length 500
                                    copypaste True

                            textbutton "Apply":
                                action Function(_vb_apply_value, vb_selected, vb_edit_value)

                        if vb_selected.startswith("persistent."):
                            text "WARNING: persistent.* changes are saved to disk and can affect future sessions." size 16
                        else:
                            text "Examples: 999   12.5   True   False   None   \"hello\"   [[1, 2, 3]" size 16

                    else:
                        text "Select a variable above, then its editable value appears here." size 18

                    if _vb_last_status:
                        text "[_vb_last_status!q]" size 17