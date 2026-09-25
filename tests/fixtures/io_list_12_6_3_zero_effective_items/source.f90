program io_list_zero_effective_items
  implicit none
  integer :: checks, i
  integer, allocatable :: empty(:)
  integer :: vals(2)
  character(len=2) :: out_zero_array, out_zero_do
  character(len=1) :: out_zero_char, z
  checks = 0
  vals = [8, 9]
  allocate(empty(0))
  empty = 8
  out_zero_array = '##'
  write(out_zero_array,'(SS,I2,I2)') empty, 7
  if (out_zero_array /= ' 7') error stop 'zero-sized array marker'
  checks = checks + 1
  out_zero_do = '##'
  write(out_zero_do,'(SS,I2,I2)') (vals(i), i = 1, 0), 7
  if (out_zero_do /= ' 7') error stop 'zero-count implied-do marker'
  checks = checks + 1
  z = 'X'
  out_zero_char = '#'
  write(out_zero_char,'(A,I1)') z(:0), 7
  if (len(z(:0)) /= 0) error stop 'zero character len'
  checks = checks + 1
  if (out_zero_char /= '7') error stop 'zero character effective item'
  checks = checks + 1
  if (checks /= 4) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 ZERO_EFFECTIVE_ITEMS OK'
end program io_list_zero_effective_items
