program i169e_blt
  implicit none
  logical :: observed
  observed = blt(1, z'80000000')
  call require_true('blt true bit-sequence comparison', observed)
  observed = blt(z'80000000', 1)
  call require_false('blt false bit-sequence comparison', observed)
  call require_true('blt result default logical', kind(blt(1, 1)) == kind(.false.))
  write(*,'(a)') 'INTRINSICS 16.9.E BLT BIT ORDER OK'
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
end program i169e_blt
