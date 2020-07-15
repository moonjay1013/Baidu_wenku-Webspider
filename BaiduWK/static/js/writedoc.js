var button_other=document.getElementById("btn_other");
button_other.onclick=function () {
        var ok = confirm("确认存储本页内容为.md文件？"); //在页面上弹出确认对话框
        if(ok){
            window.location.href="write_doc";
        }else{
            alert('已取消！')
        }
    }