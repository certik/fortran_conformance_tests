program io_list_effective_items_scalar_sequence
  implicit none
  type :: pair
    integer :: left
    integer :: right
  end type pair
  integer :: checks
  integer :: a(2)
  type(pair) :: item
  character(len=5) :: out
  checks = 0
  a = [2, 3]
  item = pair(4, 5)
  out = '#####'
  write(out,'(SS,5I1)') 1, a, item
  if (out /= '12345') error stop 'effective scalar sequence'
  checks = checks + 1
  if (checks /= 1) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 EFFECTIVE_ITEMS_SCALAR_SEQUENCE OK'
end program io_list_effective_items_scalar_sequence
