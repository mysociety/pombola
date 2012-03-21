<aside id="blog-sidebar">
	<section class="latest-posts">
		<h3>Latest Posts</h3>
		<ul>
		<?php
			global $post;
			$args = array( 'numberposts' => 5 );
			$myposts = get_posts( $args );
			foreach( $myposts as $post ) :
			setup_postdata($post);
		?>
			<li>
				<h4><a href="<?php the_permalink(); ?>"><?php the_title(); ?></a></h4>
				<p class="meta"><?php echo the_time('jS F Y');?></p>
			</li>
		<?php endforeach; ?>
		</ul>
	</section>

	<section class="sidebar-categories">
		<h3>Categories</h3>
		<ul class="sidebar-list">
		<?php
			$categories = get_categories(); 
      $base = get_bloginfo('url');
			foreach ($categories as $category) {
				echo "<li><a href='{$base}/category/{$category->category_nicename}'>{$category->cat_name}</a></li>";
			}
		?>
		</ul>
	</section>

	<section class="sidebar-archive">
		<h3>Archive</h3>
		<ul class="sidebar-list">
			<?php wp_get_archives('type=yearly'); ?>
		</ul>
	</section>
</aside>