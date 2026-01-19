Ext.ns("SynoCommunity.VNTS");

Ext.define("SynoCommunity.VNTS.AppInstance", {
    extend: "SYNO.SDS.AppInstance",
    appWindowName: "SynoCommunity.VNTS.AppWindow"
});

Ext.define("SynoCommunity.VNTS.AppWindow", {
    extend: "SYNO.SDS.AppWindow",
    constructor: function (config) {
        config = Ext.apply({
            resizable: true,
            maximizable: true,
            minimizable: true,
            width: 1100,
            height: 700,
            layout: "fit",
            padding: 0,
            items: [{
                xtype: "box",
                autoEl: {
                    tag: "iframe",
                    src: "/webman/3rdparty/VNTS/index.cgi",
                    style: "border:0; width:100%; height:100%;"
                }
            }]
        }, config);

        this.callParent([config]);
    }
});

