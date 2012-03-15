<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        <title><?php if (is_single() || is_archive()) { wp_title('',true); } else { bloginfo('name'); echo(' &#8212; '); bloginfo('description'); } ?></title>  

        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="viewport" content="width=device-width, minimum-scale=1.0, maximum-scale=1.0;">
        <meta http-equiv="cleartype" content="on">
        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">

            

        <link rel="stylesheet" type="text/css" href="http://info.mzalendo.com/static/css/basic.css" media="screen, handheld" />
        <link rel="stylesheet" type="text/css" href="http://info.mzalendo.com/static/css/mobile.css" media="only screen and (min-width: 320px) and (max-width: 640px)" />
        <link rel="stylesheet" type="text/css" href="http://evdb.mzalendo.mysociety.org/static/css/desktop.css" media="only screen and (min-width: 640px)" />

        <!--[if lt IE 9]>
            <link rel="stylesheet" type="text/css" href="http://info.mzalendo.com/static/css/desktop.css" />
        <![endif]-->

        <script src="http://info.mzalendo.com/static/js/libs/modernizr-2.0.6.custom.js"></script>
        <link rel="icon" type="image/png" href="http://info.mzalendo.com/static/images/favicon.png" />
        
        
        <!-- wp specific stuff -->
        <link rel="alternate" type="application/rss+xml" title="<?php bloginfo('name'); ?> RSS Feed" href="<?php bloginfo('rss2_url'); ?>" />
        <link rel="pingback" href="<?php bloginfo('pingback_url'); ?>" />
        <link rel="stylesheet" href="<?php bloginfo('stylesheet_url'); ?>" type="text/css" media="screen" />
        <link rel="stylesheet" type="text/css" href="<?php bloginfo('template_url'); ?>/assets/css/basic.css" media="screen, handheld" />
        <link rel="stylesheet" type="text/css" href="<?php bloginfo('template_url'); ?>/assets/css/desktop.css" media="only screen and (min-width: 640px)" />

        <link href="http://info.mzalendo.com/static/css/jquery-ui-1.8.17.custom.css" media="screen" rel="stylesheet" type="text/css" />
        
        <?php 
            //no js allowed, I want only mine here....*evil laugh*
            //wp_enqueue_script('jquery');
            //wp_head();
        ?>
    </head>
    <body>
        <header id="site-header">
            <div class="wrapper">
                <a href="http://info.mzalendo.com" id="logo">Mzalendo</a>
                <form action="http://mzalendo.com/blog" method="get" id="search">
                    <input id="main_search_box" type="text" name="s" placeholder="search&hellip;" />
                    <button type="submit">Submit</button>
                </form>
                <menu id="site-user-tools">
                    <ul>                        
                        <li class="login"><a href="http://info.mzalendo.com/accounts/login/?next=/">login</a></li>
                    </ul>
                </menu>
            </div>
        </header>

        <div id="main-menu">
            <nav class="wrapper">
                <ul>
                    <li><a href="http://info.mzalendo.com">Home</a></li>
                    <li class=""><a href="http://info.mzalendo.com/info/democracy-resources">Democracy Resources</a>
                        <ul id="democracy-resources">
                            <li>
                                <a href="http://info.mzalendo.com/info/citizens-rights">Citizens Rights &amp; Responsibilities</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/how-democracy-works">How Our Democracy Works</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/democracy-faq">Democracy FAQs</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/constitution-2010">Constitution 2010</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/election-legislation">Election Legislation</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/democracy-documents">Democracy Documents</a>
                            </li>
                        </ul>
                    </li>
                    <li><a href="http://info.mzalendo.com/person/politicians/">Politicians</a></li>
                    <li><a href="http://info.mzalendo.com/info/parliament-overview">Parliament</a>
                        <ul id="parliament-overview">
                            <li>
                                <a href="http://info.mzalendo.com/info/parliament-overview">Parliament Overview</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/ministry-overview">Ministry Overview</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/committee-overview">Committee Overview</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/bills-overview">Bills Overview</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/hansard/">Hansard</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/political-parties">Political Parties</a>
                            </li>
                        </ul>                    
                    </li>
                    <li><a href="http://info.mzalendo.com/info/places-overview">Places</a>
                        <ul id="places-overview">
                            <li>
                                <a href="http://info.mzalendo.com/info/places-overview">Places Overview</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/place/constituencies/">Constituencies</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/place/counties/">Counties</a>
                            </li>
                        </ul>
                    </li>
                    <li class=""><a href="http://info.mzalendo.com/info/2012-overview">2012</a>
                        <ul id="2012">
                            <li>
                                <a href="http://info.mzalendo.com/info/2012-overview">2012 Overview</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/2012-aspirants">Aspirants</a>
                            </li>
                        </ul>
                    </li>
                    <li><a href="http://mzalendo.com/blog/">Blog</a></li>
                    <li><a href="http://info.mzalendo.com/info/newsletter">Newsletter</a></li>
                    <li class=""><a href="http://info.mzalendo.com/info/mzalendo-overview">About</a>
                        <ul id="mzalendo-overview">
                            <li>
                                <a href="http://info.mzalendo.com/info/mzalendo-overview">Mzalendo Overview</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/site-faq">Site FAQs</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/policies">Policies</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/partners">Partners</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/scorecard-faq">Scorecard FAQs</a>
                            </li>
                            <li>
                                <a href="http://info.mzalendo.com/info/contact">Contact</a>
                            </li>
                        </ul>
                    </li>
                </ul>
            </nav>
        </div>

        <div id="page"> <!-- start #page -->
            <div class="page-wrapper wrapper"> <!-- start .page-wrapper -->