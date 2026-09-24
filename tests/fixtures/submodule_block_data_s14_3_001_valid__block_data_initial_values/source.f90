program block_data_initial_values_probe
  implicit none
  integer :: a, b
  common /initial_blk/ a, b
  if (a /= 17) error stop
  if (b /= 23) error stop
  print '(a)', 'BLOCK DATA INITIAL VALUES OK'
end program block_data_initial_values_probe
block data bd_initial_values
  implicit none
  integer :: a, b
  common /initial_blk/ a, b
  data a /17/
  data b /23/
end block data bd_initial_values
block data bd_initial_values_alt
  implicit none
  integer :: alt_a, alt_b
  common /initial_alt_blk/ alt_a, alt_b
  data alt_a /18/
  data alt_b /24/
end block data bd_initial_values_alt
