program intrinsics_16_9_j_findloc_back_argument
  implicit none
  integer :: checks
  integer :: values(4)
  integer, allocatable :: hit(:)
  checks=0
  values = [2, 6, 4, 6]
  hit = findloc(values, 6, back=.true.)
  if (any(hit /= [4])) then
    write(*,'(a)') 'I16J:findloc_back_argument:logical-scalar-back'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC BACK ARGUMENT OK'
end program intrinsics_16_9_j_findloc_back_argument
