program block_data_storage_sequence_probe
  implicit none
  integer :: a, b, c
  common /storage_blk/ a, b, c
  if (b /= 33) error stop
  print '(a)', 'BLOCK DATA STORAGE SEQUENCE OK'
end program block_data_storage_sequence_probe
block data bd_storage_sequence
  implicit none
  integer :: a, b, c
  common /storage_blk/ a, b, c
  data b /33/
end block data bd_storage_sequence
block data bd_storage_sequence_alt
  implicit none
  integer :: alt_a, alt_b, alt_c
  common /storage_alt_blk/ alt_a, alt_b, alt_c
  data alt_b /34/
end block data bd_storage_sequence_alt
