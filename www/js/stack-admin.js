var group = null;
var postData = null;

var $items = null;
var $add = null;
var $remove = null;
var $timeline = null;
var $save = null;

var initDragAndDrop = function() {
    group = $(".js-droppable-and-draggable").sortable({
        group: 'stack',
        onDragStart: function (item, container, _super) {
            // Duplicate items of the no drop area
            if(!container.options.drop)
                item.clone().insertAfter(item);
            _super(item)
        },
        onDrop: function(item, container, _super) {
            postData = group.sortable("serialize").get();
            // $.ajax({
            //     type:"POST",
            //     url: "/elections14/admin/stack/save",
            //     data: JSON.stringify(postData),
            //     dataType: "json",
            //     contentType: "application/json",
            // });
            _super(item, container)
        },
    });
}

var onItemsHover = function() {
    $(this).find('.controls').css('display', 'block');
}

var offItemsHover = function() {
    $(this).find('.controls').css('display', 'none');
}

var onAddClick = function() {
    var $item = $(this).parents('.item');
    var slide = $item.data('slide');

    var newItem = $('<li class="item" data-slide="' + slide + '">' + slide + ' <a class="remove" href="#"><span class="fa fa-times"></span></a></li>'
    )

    $timeline.append(newItem);
}

var onRemoveClick = function() {
    var $item = $(this).parents('.item');
    $item.remove();
}

var onSaveClick = function() {
    postData = group.sortable("serialize").get();
    $.ajax({
        type:"POST",
        url: "/elections14/admin/stack/save",
        data: JSON.stringify(postData),
        dataType: "json",
        contentType: "application/json",
    });
}

$(document).ready(function() {
    $timeline = $('.timeline ol')
    $items = $('.item');
    $add = $('.add');
    $remove = $('.remove');
    $save = $('.save-btn');

    $items.hover(onItemsHover, offItemsHover);
    $add.on('click', onAddClick);
    $remove.on('click', onRemoveClick);
    $save.on('click', onSaveClick);

    initDragAndDrop();
});