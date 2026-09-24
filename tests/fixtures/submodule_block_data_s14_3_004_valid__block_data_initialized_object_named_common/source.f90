program block_data_named_object_probe
  implicit none
  integer :: value
  common /named_object_blk/ value
  if (value /= 45) error stop
  print '(a)', 'BLOCK DATA NAMED OBJECT OK'
end program block_data_named_object_probe
block data bd_named_object
  implicit none
  integer :: value
  common /named_object_blk/ value
  data value /45/
end block data bd_named_object
block data bd_named_object_alt
  implicit none
  integer :: alt_value
  common /named_object_alt_blk/ alt_value
  data alt_value /46/
end block data bd_named_object_alt
