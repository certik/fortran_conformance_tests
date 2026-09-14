! rule: S7.3.2.3-005
! covers: unlimited-kind-and-length
! evidence: effect
program dynamic_unlimited_parameters
    implicit none
    integer, parameter :: default_kind = kind(0.0), double_kind = kind(0.0d0)
    real(default_kind) :: single_value = 0.0_default_kind
    real(double_kind) :: double_value = 0.0_double_kind
    character(len=2) :: short_text = 'ox'
    character(len=5) :: long_text = 'birch'
    integer :: seen = -1
    call inspect(single_value, 1, seen)
    if (seen /= 1) error stop 'default-real-call'
    seen = -1
    call inspect(double_value, 2, seen)
    if (seen /= 2) error stop 'double-real-call'
    seen = -1
    call inspect(short_text, 3, seen)
    if (seen /= 3) error stop 'short-character-call'
    seen = -1
    call inspect(long_text, 4, seen)
    if (seen /= 4) error stop 'long-character-call'
contains
    subroutine inspect(x, expected, observed)
        class(*), intent(in) :: x
        integer, intent(in) :: expected
        integer, intent(out) :: observed
        observed = -1
        select type (x)
        type is (real(kind=default_kind))
            if (expected /= 1) error stop 'wrong-default-branch'
            if (x /= 0.0_default_kind) error stop 'default-payload'
        type is (real(kind=double_kind))
            if (expected /= 2) error stop 'wrong-double-branch'
            if (x /= 0.0_double_kind) error stop 'double-payload'
        type is (character(len=*))
            select case (expected)
            case (3)
                if (len(x) /= 2) error stop 'short-length'
                if (x /= 'ox') error stop 'short-payload'
            case (4)
                if (len(x) /= 5) error stop 'long-length'
                if (x /= 'birch') error stop 'long-payload'
            case default
                error stop 'wrong-character-branch'
            end select
        class default
            error stop 'dummy-type-kind'
        end select
        observed = expected
    end subroutine
end program
