program intrinsics_16_9_j_findloc_kind_argument
  implicit none
  integer :: checks
  integer, parameter :: ik = selected_int_kind(12)
  checks=0
  if (kind(findloc([2, 4], 4, kind=ik)) /= ik) then
    write(*,'(a)') 'I16J:findloc_kind_argument:constant-kind'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC KIND ARGUMENT OK'
end program intrinsics_16_9_j_findloc_kind_argument
