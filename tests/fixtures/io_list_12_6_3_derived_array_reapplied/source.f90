program io_list_derived_array_reapplied
  implicit none
  type :: nested
    integer :: head
    integer :: values(2)
  end type nested
  integer :: checks
  type(nested) :: item
  character(len=5) :: out
  checks = 0
  item = nested(3, [4, 5])
  out = '#####'
  write(out,'(SS,3I1)') item
  if (out /= '345  ') error stop 'reapplied derived array order'
  checks = checks + 1
  if (checks /= 1) error stop 'checks'
  print '(a)', 'IO_LIST_12_6_3 DERIVED_ARRAY_REAPPLIED OK'
end program io_list_derived_array_reapplied
