program i169e_ble
  implicit none
  logical :: observed
  observed = ble(1, z'80000000')
  call require_true('ble true bit-sequence comparison', observed)
  observed = ble(z'80000000', 1)
  call require_false('ble false bit-sequence comparison', observed)
  call require_true('ble result default logical', kind(ble(1, 1)) == kind(.false.))
  write(*,'(a)') 'INTRINSICS 16.9.E BLE BIT ORDER OK'
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
end program i169e_ble
