! rule: S6.3.2.2-005
! covers: end-interface
! evidence: positive-control
program interface_spellings
  implicit none
  interface
    integer function first()
    end function first
  endinterface
  interface
    integer function second()
    end function second
  end interface
  if (first() /= 7) stop 1
  if (second() /= 9) stop 2
end program

integer function first()
  implicit none
  first = 7
end function first

integer function second()
  implicit none
  second = 9
end function second
