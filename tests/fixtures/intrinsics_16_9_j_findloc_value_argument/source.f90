program intrinsics_16_9_j_findloc_value_argument
  implicit none
  integer :: checks
  logical :: flags(4)
  integer, allocatable :: hit(:)
  checks=0
  flags = [.false., .true., .true., .false.]
  hit = findloc(flags, .true.)
  if (any(hit /= [2])) then
    write(*,'(a)') 'I16J:findloc_value_argument:logical-scalar-value'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC VALUE ARGUMENT OK'
end program intrinsics_16_9_j_findloc_value_argument
