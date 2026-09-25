program i169o_ishftc_characteristics
  implicit none
  integer, parameter :: wide_k = selected_int_kind(18)
  integer(kind=wide_k) :: wide_value
  wide_value = 3_wide_k
  call require_true('ishftc result kind is same as i expression', &
      kind(ishftc(wide_value, 1, 3)) == wide_k)
  write(*,'(a)') 'INTRINSICS 16.9.O ISHFTC CHARACTERISTICS OK'
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
end program i169o_ishftc_characteristics
