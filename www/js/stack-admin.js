var group = null;
var postData = null;

var $items = null;
var $add = null;
var $preview = null;
var $remove = null;
var $timeline = null;
var $saveForm = null;
var $stackTime = null;

var initDragAndDrop = function() {
    group = $(".js-droppable-and-draggable").sortable({
        group: 'stack',
        handle: 'span.fa-align-justify',
        onDragStart: function (item, container, _super) {
            // Duplicate items of the no drop area
            if(!container.options.drop)
                item.clone().insertAfter(item);
            _super(item)
        },
        onDrop: function(item, container, _super) {
            postData = group.sortable("serialize").get();
            _super(item, container)
        },
    });
}

var onAddClick = function() {
    var $item = $(this).parents('.item');
    var slide = $item.data('slide');
    var slideTime = parseInt($item.data('time'));
    var name = $item.data('name');
    var currentStackTime = parseInt($stackTime.text());

    var newItem = $('<li class="item" data-slide="' + slide + '" data-time="' + slideTime + '" data-name="' + name + '"><span class="dragger fa fa-align-justify"></span><a href="' + APP_CONFIG.S3_BASE_URL + '/preview/' + slide + '/index.html" target="_blank"> ' + name + ' <div class="controls"><a class="remove" href="#"><span class="fa fa-times"></span></div></li>'
    )

    $timeline.append(newItem);

    $stackTime.text(currentStackTime + slideTime);

    // reset event handlers to account for new button
    $remove = $(newItem).find('.remove');
    $remove.on('click', onRemoveClick);
}

var onRemoveClick = function() {
    var $item = $(this).parents('.item');
    var slideTime = parseInt($item.data('time'));
    var currentStackTime = parseInt($stackTime.text());

    $item.remove();

    $stackTime.text(currentStackTime - slideTime);
}

var onSaveFormSubmit = function() {
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
    $items = $('.out .item');
    $add = $('.add');
    $preview = $('.preview');
    $remove = $('.remove');
    $saveForm = $('.send-stack');
    $stackTime = $('.stack-time');

    $add.on('click', onAddClick);
    $remove.on('click', onRemoveClick);
    $saveForm.submit(onSaveFormSubmit)

    initDragAndDrop();
});
