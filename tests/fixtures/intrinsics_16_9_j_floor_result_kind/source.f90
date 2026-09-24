program intrinsics_16_9_j_floor_result_kind
  implicit none
  integer :: checks
  integer, parameter :: ik = selected_int_kind(12)
  checks=0
  if (kind(floor(3.75)) /= kind(0)) then
    write(*,'(a)') 'I16J:floor_result_kind:default-kind'
    error stop
  end if
  checks=checks+1
  if (kind(floor(3.75, kind=ik)) /= ik) then
    write(*,'(a)') 'I16J:floor_result_kind:selected-kind'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FLOOR RESULT KIND OK'
end program intrinsics_16_9_j_floor_result_kind
