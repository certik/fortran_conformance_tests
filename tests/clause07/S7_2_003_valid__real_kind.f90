! rule: S7.2-003
! covers: real-kind-selection
! evidence: effect
module type_parameters_real_generic
    implicit none
    integer, parameter :: rk = kind(0.0), dk = kind(0.0d0)
    interface identify
        module procedure ordinary_tag, wider_tag
    end interface
contains
    integer function ordinary_tag(value) result(tag)
        real(kind=rk), intent(in) :: value
        if (value /= 0.0_rk) error stop 1
        tag = 17
    end function ordinary_tag

    integer function wider_tag(value) result(tag)
        real(kind=dk), intent(in) :: value
        if (value /= 0.0_dk) error stop 2
        tag = 29
    end function wider_tag
end module type_parameters_real_generic

program type_parameters_kind_dispatch
    use type_parameters_real_generic, only: identify
    implicit none
    if (identify(0.0) /= 17) error stop 3
    if (identify(0.0d0) /= 29) error stop 4
end program type_parameters_kind_dispatch
