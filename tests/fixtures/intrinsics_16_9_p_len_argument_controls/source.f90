program i169p_len_argument_controls
  implicit none
  integer, parameter :: wide_kind = selected_int_kind(18)
  character(len=5) :: scalar = 'AB'
  character(len=6), allocatable :: unallocated_fixed
  character(len=4), pointer :: unassociated_fixed => null()
  call require_true('len accepts character string argument', len(scalar) == 5)
  call require_true('len permits nondeferred absent allocation association', &
       len(unallocated_fixed) == 6 .and. len(unassociated_fixed) == 4)
  call require_true('len kind argument is scalar integer constant', &
       kind(len(scalar, kind=wide_kind)) == wide_kind)
  write(*,'(a)') 'INTRINSICS 16.9.P LEN ARGUMENT CONTROLS OK'
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
end program i169p_len_argument_controls
