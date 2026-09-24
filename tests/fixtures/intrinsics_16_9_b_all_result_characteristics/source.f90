program intrinsics_16_9_b_all_result_characteristics
  implicit none
  integer :: checks
  logical :: mask2(2,3), vector(2), scalar_result
  logical, allocatable :: reduced(:)
  checks=0
  mask2 = reshape([.true., .true., .true., .false., .true., .true.], [2,3])
  vector = [.true., .true.]
  if (kind(all(vector)) /= kind(vector(1))) then
    write(*,'(a)') 'I16B:all_result_characteristics:same-kind'
    error stop
  end if
  checks=checks+1
  scalar_result = all(mask2)
  if (scalar_result) then
    write(*,'(a)') 'I16B:all_result_characteristics:dim-absent-scalar'
    error stop
  end if
  checks=checks+1
  scalar_result = all(vector, dim=1)
  if (.not. scalar_result) then
    write(*,'(a)') 'I16B:all_result_characteristics:rank-one-dim-scalar'
    error stop
  end if
  checks=checks+1
  reduced = all(mask2, dim=1)
  if (any(shape(reduced) /= [3])) then
    write(*,'(a)') 'I16B:all_result_characteristics:dim-shape'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (4)
  case default
    write(*,'(a)') 'I16B:all_result_characteristics:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ALL RESULT CHARACTERISTICS OK'
end program intrinsics_16_9_b_all_result_characteristics
