program i169f_count_values
  implicit none
  logical :: mask1(4), empty(0), companion(4), mask2(2,3)
    integer :: description_count, rank_one_count, empty_count
    integer, allocatable :: dim_counts(:)
  mask1 = [.true., .false., .true., .false.]
  empty = [logical ::]
  companion = [.true., .false., .true., .false.]
  mask2 = reshape([.true., .false., .true., .true., .false., .false.], [2,3])
  description_count = -777
  description_count = count([.true., .false., .true.])
  call require_true('count true value reduction description', description_count == 2)
  call require_true('count transformational dim rank reduction', &
       size(shape(count(mask2, dim=1))) == 1 .and. size(shape(count(mask2))) == 0)
  rank_one_count = -777
  rank_one_count = count(mask1)
  call require_true('count rank one true elements', rank_one_count == 2)
  empty_count = -777
  empty_count = count(empty)
  call require_true('count size zero mask zero with companion', empty_count == 0 .and. count(companion) == 2)
  dim_counts = [-777, -777, -777]
  dim_counts = count(mask2, dim=1)
  call require_true('count dim present section size', size(dim_counts) == 3)
  call require_true('count dim present section dim one', all(dim_counts == [1, 2, 0]))
  call require_true('count dim present section dim two', all(count(mask2, dim=2) == [2, 1]))
  write(*,'(a)') 'INTRINSICS 16.9.F COUNT VALUES OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_count_values
