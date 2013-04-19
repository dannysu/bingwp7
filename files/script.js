$(document).bind("pageinit",function(){
    $.mobile.ajaxEnabled = false;

    if ($('#1_credit').length > 0) {
        window.setInterval(random_flip, 5000);
    }

    $('.image').on('click',function(event){
        var id = $(this).attr('id');
        flip(id.substring(0, 1));
    });

    if (navigator.userAgent.match(/Windows Phone/)) {
        $('.imagecredit').addClass('imagecredit_wp');
    }
    else {
        $('.imagecredit').addClass('imagecredit_non_wp');
    }

    $('.imagecredit').on('click',function(event){
        var id = $(this).attr('id');
        flip(id.substring(0, 1));
    });

    $('.backimg').on('click',function(event){
        if (canShowPrevious) {
            window.location.href = previousUrl;
        }
    });
});

function flip(number) {
    if ($('#' + number + '_credit').css("visibility") == "visible") {
        $('#' + number + '_credit').animate({width: 480+"px", height: 0+"px", marginTop: 400+"px"}, 140, "swing", function(){
            $('#' + number + '_credit').css("visibility", "hidden");
            $('#' + number + '_img').animate({width: 480+"px", height: 800+"px", marginTop: 0+"px"}, 240);
        });
    }
    else {
        $('#' + number + '_img').animate({width: 480+"px", height: 0+"px", marginTop: 400+"px"}, 140, "swing", function(){
            $('#' + number + '_credit').css("visibility", "visible");
            $('#' + number + '_credit').css("marginTop", 400+"px");
            $('#' + number + '_credit').animate({width: 480+"px", height: 800+"px", marginTop: 0+"px"}, 240);
        });
    }
}

function random_flip() {
    var num_countries = 9;
    var random_number = Math.floor(Math.random()*num_countries+1);

    while ($('#' + random_number + '_credit').length <= 0)
    {
        random_number = Math.floor(Math.random()*num_countries+1);
    }

    flip(random_number);
}
