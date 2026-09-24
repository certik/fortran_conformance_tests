program block_data_multiple_named_probe
  implicit none
  integer :: left_value, right_value
  common /multi_left_blk/ left_value
  common /multi_right_blk/ right_value
  if (left_value /= 12) error stop
  if (right_value /= 34) error stop
  print '(a)', 'BLOCK DATA MULTIPLE NAMED OK'
end program block_data_multiple_named_probe
block data bd_multiple_named
  implicit none
  integer :: left_value, right_value
  common /multi_left_blk/ left_value
  common /multi_right_blk/ right_value
  data left_value /12/
  data right_value /34/
end block data bd_multiple_named
block data bd_multiple_named_alt
  implicit none
  integer :: alt_left_value, alt_right_value
  common /multi_left_alt_blk/ alt_left_value
  common /multi_right_alt_blk/ alt_right_value
  data alt_left_value /13/
  data alt_right_value /35/
end block data bd_multiple_named_alt
