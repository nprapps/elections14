var group = $(".js-droppable-and-draggable").sortable({
    group: 'stack',
    onDragStart: function (item, container, _super) {
        // Duplicate items of the no drop area
        if(!container.options.drop)
            item.clone().insertAfter(item);
        _super(item)
    },
    onDrop: function(item, container, _super) {
        var data = group.sortable("serialize").get();
        console.log(data);
        $.ajax({
            type:"POST",
            url: "/elections14/admin/stack/save",
            data: JSON.stringify(data),
            dataType: "json",
            contentType: "application/json",
        });
        _super(item, container)
    },
});

$(".js-droppable").sortable({
    group: 'stack',
    drop: false
});

$(".js-trash").sortable({
    group: 'stack'
});
