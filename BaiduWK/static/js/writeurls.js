
    var button_md=document.getElementById("btn");//动态绑定
    button_md.onclick=function() {
        var ok = confirm("确认存储全部数据为.md文件？"); //在页面上弹出确认对话框
        if(ok){
            window.location.href="write_url";
        }else{
            alert('已取消！')
        }
    }