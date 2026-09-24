program i169f_count_characteristics
  implicit none
      integer, parameter :: IK = selected_int_kind(18)
    logical :: mask1(4), mask2(2,3)
    integer :: integer_result, scalar_count
    integer, allocatable :: dim_counts(:)
    mask1 = [.true., .false., .true., .false.]
    mask2 = reshape([.true., .false., .true., .true., .false., .false.], [2,3])
    integer_result = -777
    integer_result = count(mask1)
    call require_true('count result integer exact assignment', integer_result == 2)
    call require_true('count result selected kind', kind(count(mask1, kind=IK)) == IK)
    call require_true('count result default kind', kind(count(mask1)) == kind(0))
  scalar_count = -777
  scalar_count = count(mask1)
  call require_true('count result scalar without dim', size(shape(count(mask1))) == 0 .and. scalar_count == 2)
  dim_counts = [-777, -777, -777]
  dim_counts = count(mask2, dim=1)
  call require_true('count dim result direct rank and shape', &
       size(shape(count(mask2, dim=1))) == 1 .and. size(count(mask2, dim=1)) == 3)
  call require_true('count dim result assigned size', size(dim_counts) == 3)
  call require_true('count dim result assigned values', all(dim_counts == [1, 2, 0]))
  write(*,'(a)') 'INTRINSICS 16.9.F COUNT CHARACTERISTICS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_count_characteristics
