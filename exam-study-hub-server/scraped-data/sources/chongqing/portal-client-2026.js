$(function() {
	//parent.window.$('iframe').css('height', '99%')
});

/*
* iframe 高度自适应
*/
function setIframeHeight() {
	if(browserRedirect() == "Android"){
		return false;
	}
	var iframe = parent.document.getElementById('content');
	if(iframe==null){
		return;
	}
//	 iframe.onload = function(){
		var iframeWin = iframe.contentWindow || iframe.contentDocument.parentWindow;
		if (iframeWin.document.body) {
			iframe.height = "500";
		    iframe.height = iframeWin.document.documentElement.scrollHeight || iframeWin.document.body.scrollHeight;
		}
//	 }
}

/*
 * 滚动条高度
 * */
 function scroll(){
	  var winPos = $(window).scrollTop();
	  return winPos;
 }

/*  
 * 手机端和浏览器判断
 */
 function browserRedirect() {
   var sUserAgent = navigator.userAgent.toLowerCase();
   if (/ipad|iphone|midp|rv:1.2.3.4|ucweb|android|windows ce|windows mobile/.test(sUserAgent)) {
   //跳转移动端页面
	   $("#stu_information_show").remove(); 
  	  return "Android";
   } else {
   //跳转pc端页面
	   return "pc";
   }
 }
/*$.ajax({
	async : false,
	url : "/static/js/czstu/a_header_home.html",
	success : function(result) {
		  $("#myDiv").html(result);
	}
});*/

function handleResult(result) {
	if (typeof (result.status) == "undefined") {
		window.location.href = "/czPage/index";
	}
	try {
		var resultstatus = result.status;
		if (resultstatus == 200) {
			layer.open({
				title: ('成功'),
			    content:result.responseText
			    ,btn: '我知道了'
			  });
		}  else if (resultstatus == 202) {
			layer.open({
				title: ['错误','background-color: #FF4351; color:#fff;'],
				content:result.responseText
			    ,btn: '我知道了'
			  });
		}else if (resultstatus == 201) {
			layer.open({
				title: ['错误','background-color: #FF4351; color:#fff;'],
			    content:result.responseText
			    ,btn: '我知道了'
			  });
		}else if (resultstatus == 203) {
			layer.open({
				title: ['错误','background-color: #FF4351; color:#fff;'],
			    content:result.responseText
			    ,btn: ['知道了']
		    	,yes: function(index){
		    		window.location.href = "/czPage/index";
		    	}
			  });
		}else{
			layer.open({
				title: ['操作错误','background-color: #FF4351; color:#fff;'],
				content:'操作错误',
			    btn: '我知道了'
			  });
		}
	} catch (err) {
		window.location.href = "/czPage/index";
	}
}


$(document).on("click", "#navButton", function() {
	$("#navtree").show();
});


$(function() {
	$('#navtree').hover(function() {
	    // 鼠标移入时添加hover类
	}, function() {
	    // 鼠标移出时移出hover类
		$("#navtree").hide();
	});
});

layui.use('element', function(){
	  var element = layui.element;
});
function handleSUCCESSResult(result) {
	if (!jQuery.isEmptyObject(result)) {
		if (result.status == '200') {

		} else if (result.status == '400') {
			layer.msg("400");
		} else if (result.status == '401') {
			pagetologin();
		} else if (result.status == '402') {
			layer.msg("402");
		} else if (result.status == '403') {
			layer.msg("403");
		} else if (result.status == '404') {
			layer.msg("404");
		}else if (result.status == '500') {
			if (!jQuery.isEmptyObject(result.msg)) {
				layer.msg(result.msg);
			}else{
				layer.msg("500");
			}
		} else if (result.status == 401) {
			pagetologin();
		}  else {

		}
	}
}

function pagetologin() {
	layer.alert('登录已经过期，请重新登录', {
		skin : 'layui-layer-molv', //样式类名
		closeBtn : 0
	}, function() {
		window.sessionStorage.clear();
		if(window.top !== window.self){
			window.top.location.href = "/";
		}else{
			window.location.href = "/";
		}
		
	});
}

function getcqzkip() {
    var cqzkinfoabc = window.sessionStorage.getItem("cqzkinfoabc");
    var cqzkinfoabc_time = window.sessionStorage.getItem("cqzkinfoabc_time");
    var now = Date.now();
    var expireTime = 5 * 60 * 1000; // 5分钟

    // 如果缓存存在且未过期，直接返回
    if (cqzkinfoabc && cqzkinfoabc_time && (now - parseInt(cqzkinfoabc_time) < expireTime)) {
        return cqzkinfoabc;
    }
    // 缓存不存在或已过期，重新获取
    $.ajax({
        cache: false,
        url: 'https://svc.cqzk.com.cn/api/ip',
        method: 'POST',
        timeout: 3000,
        success: function(res) {
            var ip = res.data ? res.data.ip : '';
            if (ip) {
                window.sessionStorage.setItem("cqzkinfoabc", ip);
                window.sessionStorage.setItem("cqzkinfoabc_time", String(Date.now()));
            }
        },
        complete: function(xhr, data) {
            // 完成回调
        },
        error: function(data) {
            // 错误处理
        }
    });
}
function getcqzkipval() {
    var cqzkinfoabc = window.sessionStorage.getItem("cqzkinfoabc");
    var cqzkinfoabc_time = window.sessionStorage.getItem("cqzkinfoabc_time");
    var now = Date.now();
    var expireTime = 5 * 60 * 1000; // 5分钟

    // 如果缓存存在且未过期，直接返回
    if (cqzkinfoabc && cqzkinfoabc_time && (now - parseInt(cqzkinfoabc_time) < expireTime)) {
        return cqzkinfoabc;
    }
    
    var newip="0.0.0.0";
    // 缓存不存在或已过期，重新获取
    $.ajax({
        cache: false,
        url: 'https://svc.cqzk.com.cn/api/ip',
        method: 'POST',
        async: false,
        timeout: 3000,
        success: function(res) {
            var ip = res.data ? res.data.ip : '';
            if (ip) {
                window.sessionStorage.setItem("cqzkinfoabc", ip);
                window.sessionStorage.setItem("cqzkinfoabc_time", String(Date.now()));
                newip=ip;
            }
        },
        complete: function(xhr, data) {
            // 完成回调
        },
        error: function(data) {
            // 错误处理
        }
    });
    return newip;
}