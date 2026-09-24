program intrinsics_16_9_j_findloc_result_kind
  implicit none
  integer :: checks
  integer, parameter :: ik = selected_int_kind(12)
  checks=0
  if (kind(findloc([2, 4], 4)) /= kind(0)) then
    write(*,'(a)') 'I16J:findloc_result_kind:default-kind'
    error stop
  end if
  checks=checks+1
  if (kind(findloc([2, 4], 4, kind=ik)) /= ik) then
    write(*,'(a)') 'I16J:findloc_result_kind:selected-kind'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FINDLOC RESULT KIND OK'
end program intrinsics_16_9_j_findloc_result_kind
