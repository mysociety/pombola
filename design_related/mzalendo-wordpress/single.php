<?php get_header();?>
	<div id="blog-posts" class="single">
		<?php if ( have_posts() ) : while ( have_posts() ) : the_post(); ?>
			<div id="post-<?php the_ID(); ?>" <?php post_class(); ?> >
				<h2><?php the_title(); ?></h2>
				<p class="meta">Posted by <?php echo the_author_posts_link();?> on <?php echo the_time('jS F Y');?></p>
				<p class="comments-link"><?php comments_popup_link('No Comments', '1 Comment', '% Comments');?></p>
				<section>
					<p class="categories">Categories: &nbsp;&nbsp;<?php echo the_category(' ');?></p>

					<div class="post-entry">
						<?php the_content('Read more &raquo;'); ?>
						<?php wp_link_pages(); ?>
					</div>
				</section>
			</div>
			<?php //previous_post_link('%link'); ?>
			<?php //next_post_link('%link'); ?>
			<?php comments_template(); ?>
		<?php endwhile; else: ?>
			<h2>Not Found</h2>
			<p>Sorry, but you are looking for something that isn't here.</p>
			<?php get_search_form(); ?>
		<?php endif; ?>
	</div>
	<div class="social-and-tools">
	    <div class="fb-like" data-send="false" data-layout="button_count" data-width="95" data-show-faces="false"></div>
	    
	    <a href="https://twitter.com/share" class="twitter-share-button" data-count="horizontal" data-via="MzalendoWatch">Tweet</a>
	</div>
	
	<?php get_sidebar(); ?>	
<?php get_footer(); ?>