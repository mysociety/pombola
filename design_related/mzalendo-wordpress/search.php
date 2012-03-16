<?php get_header();?>
	<div id="blog-title-space" >
		<h1>Search Result for '<?php /* Search Count */ $allsearch = &new WP_Query("s=$s&showposts=-1"); $key = wp_specialchars($s, 1); $count = $allsearch->post_count; _e(''); _e('<span class="search-terms">'); echo $key; _e('</span>'); _e("'</h1><p>"); echo $count . ' '; _e('articles'); wp_reset_query(); ?></p>
	</div>

	<div id="blog-posts">
		<?php if ( have_posts() ) : while ( have_posts() ) : the_post(); ?>
			<div id="post-<?php the_ID(); ?>" <?php post_class(); ?>>
				<h2><a href="<?php the_permalink() ?>" rel="bookmark" title="Permanent Link to <?php the_title(); ?>"><?php the_title(); ?></a></h2>
				<p class="meta">Posted by <?php echo the_author_posts_link();?> on <?php echo the_time('jS F Y');?></p>
				<p class="comments-link"><?php comments_popup_link('No Comments', '1 Comment', '% Comments');?></p>
				<section>
					<p class="categories">Categories: <?php echo the_category(' ');?></p>

					<div class="post-entry">
						<?php the_excerpt(); ?>
					</div>
				</section>
			</div>
		<?php endwhile; else: ?>
			<h2>Not Found</h2>
			<p>Sorry, but you are looking for something that isn't here.</p>
			<?php get_search_form(); ?>
		<?php endif; ?>

		<?php if (  $wp_query->max_num_pages > 1 ) : ?>
			<div class="pagination">
				<?php previous_posts_link( __( 'Previous' ) ); ?>
				<?php next_posts_link( __( 'Next' ) ); ?>
			</div>
		<?php endif; ?>
	</div>

	<?php get_sidebar(); ?>

<?php get_footer(); ?>