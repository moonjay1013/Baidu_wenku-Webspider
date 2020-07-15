var button_ppt=document.getElementById("btn_ppt");
button_ppt.onclick=function () {
        var ok = confirm("确认存储当前的链接为图片？"); //在页面上弹出确认对话框
        if(ok){
            window.location.href="write_ppt";
        }else{
            alert('已取消！')
        }
    }