program i169f_count_arguments
  implicit none
      integer, parameter :: IK = selected_int_kind(18)
    logical :: mask1(3), mask2(2,3)
    integer :: mask_control, dim_value
    integer, allocatable :: dim_counts(:), pointer_counts(:)
    integer, target :: dim_target
    integer, pointer :: dim_ptr
  mask1 = [.true., .false., .true.]
  mask2 = reshape([.true., .false., .true., .true., .false., .false.], [2,3])
  mask_control = -77
  mask_control = count(mask1)
  call require_true('count logical mask argument', mask_control == 2)
  dim_value = 1
  dim_counts = [-77, -77, -77]
  dim_counts = count(mask2, dim=dim_value)
  call require_true('count dim scalar in range size', size(dim_counts) == 3)
  call require_true('count dim scalar in range values', all(dim_counts == [1, 2, 0]))
  dim_target = 1
  dim_ptr => dim_target
  pointer_counts = [-77, -77, -77]
  pointer_counts = count(mask2, dim=dim_ptr)
  call require_true('count associated pointer dim actual size', size(pointer_counts) == 3)
  call require_true('count associated pointer dim actual values', all(pointer_counts == [1, 2, 0]))
  call require_true('count kind constant argument', kind(count(mask1, kind=IK)) == IK)
  write(*,'(a)') 'INTRINSICS 16.9.F COUNT ARGUMENTS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
end program i169f_count_arguments
