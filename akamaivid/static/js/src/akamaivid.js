/* Javascript for AkamaiVidXBlock. */
function AkamaiVidXBlock(runtime, element) {

    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
          (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
              m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
          })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');

      ga('create', 'UA-40755110-27', 'auto');
      ga('send', 'pageview');


    $(function ($) {
        /* Here's where you'd do things on page load. */
        var acl = document.getElementById("acl").innerHTML;
        var token = document.getElementById("token").innerHTML;
        var image = document.getElementById("image").innerHTML;
        var vttFile = document.getElementById("vttFile").innerHTML;
        var link = "https://ehl_ondemand-vh.akamaihd.net/i/" + acl + "/master.m3u8?" + token;
        console.log(link);
        window.jwplayer.key = "6rBI0CGUM9xu3WEhVlz1CyceuwyqRt4A3bkQx36Asb0=";
        var setup = {
            "file": link,
            "image": image, 
            "width": "100%",
            "autostart": false,
            "abouttext": "Digotel Sarl 2017",
            "aspectratio": "16:9",
            "hlshtml": true,
            "ga": {}, 
        }
        if(vttFile.length > 5){
            setup.tracks = [{
                file: vttFile,
                label: "English",
                kind: "captions",
                default: false
            }]
        }
        window.jwplayer("jwPlayerDiv").setup(setup);


    });
}
