program i169o_lbound_characteristics
  implicit none
  integer, parameter :: wide_k = selected_int_kind(18)
  integer :: a(-3:4, 7:9)
  call require_true('lbound result integer kind default or kind argument', &
      kind(lbound(a)) == kind(0) .and. kind(lbound(a, kind=wide_k)) == wide_k)
  call require_true('lbound result scalar when dim present', &
      rank(lbound(a, dim=2)) == 0 .and. lbound(a, dim=2) == 7)
  call require_true('lbound result rank one size rank when dim absent', &
      rank(lbound(a)) == 1 .and. size(lbound(a)) == rank(a) .and. lbound(lbound(a), dim=1) == 1)
  write(*,'(a)') 'INTRINSICS 16.9.O LBOUND CHARACTERISTICS OK'
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
end program i169o_lbound_characteristics
