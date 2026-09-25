program io_list_allocatable_io
  implicit none
  integer :: checks
  character(len=2) :: rec
  character(len=4) :: out
  integer, allocatable :: x
  checks = 0
  rec = '26'
  out = '####'
  allocate(x)
  x = -626
  if (.not. allocated(x)) error stop 'allocatable not allocated before input'
  checks = checks + 1
  if (x /= -626) error stop 'allocatable pre-read sentinel'
  checks = checks + 1
  read(rec,*) x
  if (x /= 26) error stop 'allocatable input value'
  checks = checks + 1
  x = 37
  write(out,'(SS,I2)') x
  if (out /= '37  ') error stop 'allocatable output value'
  checks = checks + 1
  if (checks /= 4) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 ALLOCATABLE_IO OK'
end program io_list_allocatable_io
