import bi

multisite_datasources["bi_aggregations"] = {
    "title"       : "BI Aggregations",
    "table"       : bi.table, 
    "infos"       : [ "aggr" ],
    "keys"        : [],
}

multisite_datasources["bi_host_aggregations"] = {
    "title"       : "BI Host Aggregations",
    "table"       : bi.host_table, 
    "infos"       : [ "host", "aggr" ],
    "keys"        : [],
}

def paint_aggr_state_short(state, assumed = False):
    if state == None:
        return "", ""
    else:
        name = nagios_short_state_names[state]
        classes = "state svcstate state%s" % state
        if assumed:
            classes += " assumed"
        return classes, name

multisite_painters["aggr_state"] = {
    "title"   : "Aggregated state",
    "short"   : "State",
    "columns" : [ "aggr_effective_state" ],
    "paint"   : lambda row: paint_aggr_state_short(row["aggr_effective_state"], row["aggr_effective_state"] != row["aggr_state"])
}

multisite_painters["aggr_real_state"] = {
    "title"   : "Aggregated real state (never assumed)",
    "short"   : "R.State",
    "columns" : [ "aggr_state" ],
    "paint"   : lambda row: paint_aggr_state_short(row["aggr_state"])
}

multisite_painters["aggr_assumed_state"] = {
    "title"   : "Aggregated assumed state",
    "short"   : "Assumed",
    "columns" : [ "aggr_assumed_state" ],
    "paint"   : lambda row: paint_aggr_state_short(row["aggr_assumed_state"])
}


multisite_painters["aggr_group"] = {
    "title"   : "Aggregation group",
    "short"   : "Group",
    "columns" : [ "aggr_group" ],
    "paint"   : lambda row: ("", row["aggr_group"])
}

multisite_painters["aggr_name"] = {
    "title"   : "Aggregation name",
    "short"   : "Aggregation",
    "columns" : [ "aggr_name" ],
    "paint"   : lambda row: ("", row["aggr_name"])
}

multisite_painters["aggr_output"] = {
    "title"   : "Aggregation status output",
    "short"   : "Output",
    "columns" : [ "aggr_output" ],
    "paint"   : lambda row: ("", row["aggr_output"])
}

def paint_aggr_hosts(row):
    h = []
    for host in row["aggr_hosts"]:
        url = html.makeuri([("view_name", "host"), ("host", host)])
        h.append('<a href="%s">%s</a>' % (url, host))
    return "", " ".join(h)

multisite_painters["aggr_hosts"] = {
    "title"   : "Aggregation: affected hosts",
    "short"   : "Hosts",
    "columns" : [ "aggr_hosts" ],
    "paint"   : paint_aggr_hosts,
}


multisite_painter_options["aggr_expand"] = {
 "title"   : "Initial expansion of aggregations",
 "default" : "0",
 "values"  : [ ("0", "collapsed"), ("1", "first level"), ("2", "two levels"), ("3", "three levels"), ("999", "complete")]
}

multisite_painter_options["aggr_onlyproblems"] = {
 "title"   : "Show only problems",
 "default" : "0",
 "values"  : [ ("0", "show all"), ("1", "show only problems")]
}

def render_bi_state(state):
    return { bi.OK:      "OK", 
             bi.WARN:    "WA",
             bi.CRIT:    "CR", 
             bi.UNKNOWN: "UN",
             bi.MISSING: "MI",
             bi.UNAVAIL: "NA",
    }[state]

def render_assume_icon(site, host, service):
    ass = bi.g_assumptions.get((site, host, service))
    mousecode = \
       'onmouseover="this.style.cursor=\'pointer\';" ' \
       'onmouseout="this.style.cursor=\'auto\';" ' \
       'title="Assume another state for this item" ' \
       'onclick="toggle_assumption(this, %s, %s, %s);" ' % \
         (repr(site), repr(str(host)), service == None and 'null' or repr(str(service)))
    current = str(ass).lower()
    return '<img state="%s" class=assumption %s src="images/assume_%s.png">' % (current, mousecode, current)

def paint_aggregated_tree_state(row):
    only_problems = get_painter_option("aggr_onlyproblems") == "1"

    def render_subtree(tree, level=1):
        nodes = tree[6]
        is_leaf = nodes == None
        if is_leaf:
            h = '<div class="aggr leaf">'
            site = 'local'
            host = tree[4][0]
            service = tree[2]
            content = render_assume_icon(site, host, service) 
            # site fehlt!
            if service:
                url = html.makeuri([("view_name", "service"), ("host", host), ("service", service)])
            else:
                url = html.makeuri([("view_name", "hoststatus"), ("host", host)])
                service = "Host status"
            content += '<a href="%s">%s</a>' % (url, service)
            mousecode = ""
        else:
            mousecode = \
               'onmouseover="this.style.cursor=\'pointer\';" ' \
               'onmouseout="this.style.cursor=\'auto\';" ' \
               'onclick="toggle_subtree(this);" '
            h = '<div class="aggr tree">'
            content = tree[2]

        state = tree[0]
        assumed_state = tree[1]
        if assumed_state != None:
            effective_state = assumed_state 
        else:
            effective_state = state

        if (effective_state != state):
            addclass = " assumed"
        else:
            addclass = ""
        h += '<div style="float: left" class="content state state%d%s">%s</div>' \
             % (effective_state, addclass, render_bi_state(effective_state))
        h += '<div style="float: left;" %s class="content name">%s</div>' % (mousecode, content)
        output = tree[3]
        if output:
            output = "&nbsp;&diams; " + output
        else:
            output = "&nbsp;"
        h += '<div class="content output">%s</div>' % output

        if nodes != None:
            expansion_level = int(get_painter_option("aggr_expand"))
            if level > expansion_level:
                style = 'style="display: none" '
            else:
                style = ''
            h += '<div %sclass="subtree">' % style
            for node in tree[6]:
                if only_problems and node[0] == 0:
                    continue
                h += render_subtree(node, level + 1)
            h += "</div>"
        return h + "</div>"

    tree = row["aggr_treestate"]
    return "", render_subtree(tree)

multisite_painters["aggr_treestate"] = {
    "title"   : "Aggregation: complete tree",
    "short"   : "Tree",
    "columns" : [ "aggr_treestate" ],
    "options" : [ "aggr_expand", "aggr_onlyproblems" ],
    "paint"   : paint_aggregated_tree_state,
}

