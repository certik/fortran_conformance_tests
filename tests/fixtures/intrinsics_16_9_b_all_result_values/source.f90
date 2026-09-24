program intrinsics_16_9_b_all_result_values
  implicit none
  integer :: checks
  logical :: all_true(2), has_false(3), empty(0), mask2(2,3)
  logical, allocatable :: reduced(:)
  checks=0
  all_true = [.true., .true.]
  has_false = [.true., .false., .true.]
  mask2 = reshape([.true., .true., .true., .false., .true., .true.], [2,3])
  if (.not. all(all_true)) then
    write(*,'(a)') 'I16B:all_result_values:all-true'
    error stop
  end if
  checks=checks+1
  if (.not. all(empty)) then
    write(*,'(a)') 'I16B:all_result_values:zero-size-true'
    error stop
  end if
  checks=checks+1
  if (all(has_false)) then
    write(*,'(a)') 'I16B:all_result_values:false-element'
    error stop
  end if
  checks=checks+1
  reduced = all(mask2, dim=1)
  if (any(reduced .neqv. [.true., .false., .true.])) then
    write(*,'(a)') 'I16B:all_result_values:dim-sections'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (4)
  case default
    write(*,'(a)') 'I16B:all_result_values:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ALL RESULT VALUES OK'
end program intrinsics_16_9_b_all_result_values
