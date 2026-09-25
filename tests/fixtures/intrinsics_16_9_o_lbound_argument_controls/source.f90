program i169o_lbound_argument_controls
  implicit none
  integer, parameter :: wide_k = selected_int_kind(18)
  integer, allocatable :: alloc_array(:)
  integer, target :: target_array(-4:-2) = [41, 42, 43]
  integer, pointer :: pointer_array(:)
  integer :: rank_two(-3:4, 7:9)
  integer, target :: dim_target = 2
  integer :: plain_dim = 2
  integer, pointer :: dim_pointer
  integer, allocatable :: dim_alloc
  allocate(alloc_array(-2:2))
  pointer_array => target_array
  call require_true('lbound requires allocated or associated array arguments positively', &
      lbound(alloc_array, dim=1) == -2 .and. lbound(pointer_array, dim=1) == -4)
  call require_true('lbound dim is integer scalar in rank range', &
      lbound(rank_two, dim=1) == -3 .and. lbound(rank_two, dim=2) == 7)
  dim_pointer => dim_target
  allocate(dim_alloc)
  dim_alloc = 1
  call require_true('lbound dim corresponding actual present associated allocated', &
      plain_dim_result(rank_two, plain_dim) == 7 .and. pointer_dim_result(rank_two, dim_pointer) == 7 .and. &
      alloc_dim_result(rank_two, dim_alloc) == -3)
  call require_true('lbound kind is scalar integer constant expression', &
      kind(lbound(rank_two, kind=wide_k)) == wide_k)
  write(*,'(a)') 'INTRINSICS 16.9.O LBOUND ARGUMENT CONTROLS OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
  integer function plain_dim_result(array, dim)
    integer, intent(in) :: array(-3:, 7:)
    integer, intent(in) :: dim
    plain_dim_result = lbound(array, dim=dim)
  end function plain_dim_result
  integer function pointer_dim_result(array, dim)
    integer, intent(in) :: array(-3:, 7:)
    integer, pointer, intent(in) :: dim
    pointer_dim_result = lbound(array, dim=dim)
  end function pointer_dim_result
  integer function alloc_dim_result(array, dim)
    integer, intent(in) :: array(-3:, 7:)
    integer, allocatable, intent(in) :: dim
    alloc_dim_result = lbound(array, dim=dim)
  end function alloc_dim_result
end program i169o_lbound_argument_controls
