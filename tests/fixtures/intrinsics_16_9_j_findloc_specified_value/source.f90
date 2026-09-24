program intrinsics_16_9_j_findloc_specified_value
  implicit none
  integer :: checks
  integer :: values(4)
  integer, allocatable :: hit(:)
  checks=0
  values = [3, 8, 9, 8]
  hit = findloc(values, 9)
  if (any(hit /= [3])) then
    write(*,'(a)') 'I16J:findloc_specified_value:specified-value'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC SPECIFIED VALUE OK'
end program intrinsics_16_9_j_findloc_specified_value
