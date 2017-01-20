/* Javascript for AkamaiVidXBlock. */
var asdasd;
function AkamaiVidEditXBlock(runtime, element) {

    function arreglarUrl(s){
        if(s.indexOf("https://") == 0 || s.indexOf("http://") == 0){
            return s;
        }
        if(s.indexOf("http://") < 0){   
            return "http://"+s;
        }
    }


    $(function ($) {
        asdasd = runtime;
        var save = document.getElementById("save");

        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
        save.addEventListener("click",function(){
            var title = document.getElementById("videoTitle").value;
            var fileName = document.getElementById("videoFileName").value;
            var imageUrl = document.getElementById("imageUrl").value;
            var vttFile = document.getElementById("vttFileStudio").value;
            var data = {
                "title" : title && title.trim(), 
                "file": fileName.trim(),
                "image": imageUrl && arreglarUrl(imageUrl.trim()),
                "vttFile": vttFile.trim(),
            }
            $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
                if (response.result === 'success') {
                    window.location.reload(false);
                } else {
                    alert("error");
                }
            });
        });
    });
}
